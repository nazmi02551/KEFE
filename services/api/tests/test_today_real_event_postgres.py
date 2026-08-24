from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_content_configuration import (
    PostgresContentConfigurationRepository,
)
from kefe_api.infrastructure.postgres_flow_pinned_content_authoring import (
    PostgresFlowPinnedContentAuthoringRepository,
)
from kefe_api.infrastructure.postgres_perspective_decision import (
    PostgresPerspectiveDecisionRepository,
)
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    AuthoringContextBlock,
    AuthoringIssue,
    AuthoringQuestion,
    AuthoringSourceReference,
    CaseIdentity,
    ContentLifecycle,
)
from kefe_api.modules.content_authoring.registry import default_authoring_registry
from kefe_api.modules.content_authoring.service import ContentAuthoringService
from kefe_api.modules.content_configuration.bootstrap import (
    build_default_content_configuration,
)
from kefe_api.modules.content_configuration.publication_resolver import (
    ContentConfigurationPublicationResolver,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _service() -> tuple[object, ContentAuthoringService]:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    repository = PostgresFlowPinnedContentAuthoringRepository(engine)
    configuration_repository = PostgresContentConfigurationRepository(engine)
    configuration_repository.seed_if_empty(build_default_content_configuration())
    service = ContentAuthoringService(
        repository,
        default_authoring_registry(),
        ContentConfigurationPublicationResolver(configuration_repository),
    )
    return engine, service


def _real_event_version(case_id) -> AuthoringCaseVersion:
    source_id = uuid4()
    question = AuthoringQuestion(
        id=uuid4(),
        stable_code="PRIMARY_DECISION",
        prompt="Which option would you choose?",
        response_type="SINGLE_CHOICE",
        response_schema={"options": ["A", "B"]},
    )
    return AuthoringCaseVersion(
        id=uuid4(),
        case_id=case_id,
        version_no=1,
        state=ContentLifecycle.DRAFT,
        title="Governed real-event projection test",
        summary="A source-verified real-world event used to verify the Today projection.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(
            AuthoringIssue(
                id=uuid4(),
                code="PRIMARY_ISSUE",
                title="Primary decision issue",
                questions=(question,),
            ),
        ),
        sources=(
            AuthoringSourceReference(
                id=source_id,
                source_kind="OFFICIAL",
                locator="https://example.test/real-event-source",
                title="Official source",
                publisher="Example Authority",
                claim_status="VERIFIED",
                verified=True,
            ),
        ),
        context_blocks=(
            AuthoringContextBlock(
                id=uuid4(),
                title="Verified context",
                body="A verified contextual fact for the real-world event.",
                disclosure_level="ESSENTIAL",
                claim_status="VERIFIED",
                source_ids=(source_id,),
            ),
        ),
        is_fact_bearing=True,
        is_real_event=True,
    )


def test_real_event_editorial_truth_survives_publication_projection() -> None:
    engine, service = _service()
    identity = CaseIdentity(id=uuid4(), slug=f"today-{uuid4().hex[:10]}")
    draft = _real_event_version(identity.id)

    service.create_case(identity=identity, initial_version=draft, actor_ref="editor:test")
    service.submit_for_review(draft.id, actor_ref="editor:test")
    service.approve(draft.id, actor_ref="reviewer:test")
    published = service.publish(draft.id, actor_ref="publisher:test")

    consumer = PostgresPerspectiveDecisionRepository(engine).get_case_version(published.id)
    assert consumer is not None
    assert consumer.is_real_event is True

    with engine.connect() as connection:
        projected = connection.execute(
            text(
                """
                SELECT is_real_event
                FROM content.case_version
                WHERE id = :version_id
                """
            ),
            {"version_id": published.id},
        ).scalar_one()
    assert projected is True
