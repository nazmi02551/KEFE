from __future__ import annotations

import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_content_configuration import (
    PostgresContentConfigurationRepository,
)
from kefe_api.modules.admin_security.models import (
    AdminPrincipal,
    AdminRole,
    AdminSessionResolution,
    AdminSessionStatus,
)
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_configuration.bootstrap import build_default_content_configuration
from kefe_api.modules.content_configuration.models import (
    ContentConfigLifecycle,
    FlowStepDefinition,
    FlowTemplateDefinition,
)
from kefe_api.modules.content_configuration.service import ContentConfigurationService

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


class StaticResolver:
    def resolve(self, session_token: str) -> AdminSessionResolution:
        return AdminSessionResolution(AdminSessionStatus.INVALID)

    def mark_seen(self, session_id: UUID, *, seen_at: datetime) -> None:
        return None


def _principal() -> AdminPrincipal:
    now = datetime.now(UTC)
    return AdminPrincipal(
        admin_subject_id=uuid4(),
        session_id=uuid4(),
        roles=frozenset({AdminRole.TAXONOMY_MANAGER}),
        direct_capabilities=frozenset(),
        authenticated_at=now - timedelta(minutes=10),
        mfa_satisfied_at=now - timedelta(minutes=10),
        step_up_at=now - timedelta(minutes=1),
        expires_at=now + timedelta(hours=10),
        last_seen_at=now - timedelta(minutes=1),
    )


def _service(repository: PostgresContentConfigurationRepository) -> ContentConfigurationService:
    security = AdminSecurityService(
        session_resolver=StaticResolver(),
        policy=default_admin_security_policy(),
    )
    return ContentConfigurationService(repository=repository, security=security)


def test_postgres_configuration_publish_and_rollback_are_durable() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(database_url)
    repository = PostgresContentConfigurationRepository(engine)
    seed = build_default_content_configuration()
    repository.seed_if_empty(seed)
    service = _service(repository)
    principal = _principal()

    original = service.current()
    assert original.primitives == seed.primitives
    assert original.capabilities == seed.capabilities
    assert original.flow_templates == seed.flow_templates

    draft = service.create_draft_from_current(principal)
    custom_flow = FlowTemplateDefinition(
        code="POSTGRES_GENERIC_FLOW",
        version_no=1,
        label_key="flow.postgres_generic_flow",
        entry_step_code="CONTEXT",
        steps=(
            FlowStepDefinition(
                code="CONTEXT",
                primitive_code="CONTEXT",
                capability_codes=("STAKEHOLDER_ANALYSIS",),
                next_step_codes=("DECISION",),
            ),
            FlowStepDefinition(
                code="DECISION",
                primitive_code="DECISION",
                capability_codes=("COMMIT_FIRST", "CONFIDENCE_CAPTURE"),
            ),
        ),
    )
    updated = replace(draft, flow_templates=(*draft.flow_templates, custom_flow))
    saved = service.save_draft(principal, updated)

    persisted_draft = repository.get(saved.id)
    assert persisted_draft is not None
    assert persisted_draft.primitives == saved.primitives
    assert persisted_draft.capabilities == saved.capabilities
    assert persisted_draft.flow_templates == saved.flow_templates
    assert persisted_draft.flow_templates[-1] == custom_flow

    published = service.publish(principal, saved.id)

    assert published.state is ContentConfigLifecycle.PUBLISHED
    assert service.current().id == published.id
    persisted_published = repository.get(published.id)
    assert persisted_published is not None
    assert persisted_published.flow_templates == published.flow_templates
    assert persisted_published.flow_templates[-1].steps[0].capability_codes == (
        "STAKEHOLDER_ANALYSIS",
    )

    persisted_original = repository.get(original.id)
    assert persisted_original is not None
    assert persisted_original.state is ContentConfigLifecycle.SUPERSEDED

    rollback = service.create_rollback_draft(
        principal,
        original.id,
        rationale="Restore known-good composable configuration",
    )
    assert rollback.cloned_from_version_id == original.id
    assert rollback.state is ContentConfigLifecycle.DRAFT
    assert rollback.flow_templates == original.flow_templates
    assert service.current().id == published.id

    audit_commands = [entry.command for entry in repository.list_audit()]
    assert audit_commands == [
        "CREATE_DRAFT_FROM_CURRENT",
        "SAVE_DRAFT",
        "PUBLISH",
        "CREATE_ROLLBACK_DRAFT",
    ]

    with engine.connect() as connection:
        published_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM content_config.configuration_version
                WHERE lifecycle_state = 'PUBLISHED'
                """
            )
        ).scalar_one()
        stored = connection.execute(
            text(
                """
                SELECT aggregate
                FROM content_config.configuration_version
                WHERE id = :version_id
                """
            ),
            {"version_id": published.id},
        ).scalar_one()

    assert published_count == 1
    assert stored["flow_templates"][-1]["code"] == "POSTGRES_GENERIC_FLOW"
    assert stored["capabilities"]
    assert stored["primitives"]
