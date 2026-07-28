from __future__ import annotations

import os
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
from kefe_api.modules.content_configuration.models import ContentConfigLifecycle
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


def test_postgres_configuration_publish_and_rollback_are_durable() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(database_url)
    repository = PostgresContentConfigurationRepository(engine)
    repository.seed_if_empty(build_default_content_configuration())
    security = AdminSecurityService(
        session_resolver=StaticResolver(),
        policy=default_admin_security_policy(),
    )
    service = ContentConfigurationService(repository=repository, security=security)
    principal = _principal()

    original = service.current()
    draft = service.create_draft_from_current(principal)
    published = service.publish(principal, draft.id)

    assert published.state is ContentConfigLifecycle.PUBLISHED
    assert service.current().id == published.id
    persisted_original = repository.get(original.id)
    assert persisted_original is not None
    assert persisted_original.state is ContentConfigLifecycle.SUPERSEDED

    rollback = service.create_rollback_draft(
        principal,
        original.id,
        rationale="Restore known-good configuration",
    )
    assert rollback.cloned_from_version_id == original.id
    assert rollback.state is ContentConfigLifecycle.DRAFT
    assert service.current().id == published.id

    audit_commands = [entry.command for entry in repository.list_audit()]
    assert audit_commands == [
        "CREATE_DRAFT_FROM_CURRENT",
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
    assert published_count == 1
