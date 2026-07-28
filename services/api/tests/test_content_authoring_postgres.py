from __future__ import annotations

import os
from dataclasses import replace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_content_authoring import (
    PostgresContentAuthoringRepository,
)
from kefe_api.infrastructure.postgres_context import PostgresContextRepository
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

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _aggregate(case_id):
    source_id = uuid4()
    source = AuthoringSourceReference(
        id=source_id,
        source_kind="OFFICIAL",
        locator="https://example.test/official-source",
        title="Official source",
        publisher="Example Authority",
        claim_status="VERIFIED",
        verified=True,
    )
    block = AuthoringContextBlock(
        id=uuid4(),
        title="What is known",
        body="A verified contextual fact for the low-risk test Case.",
        disclosure_level="ESSENTIAL",
        claim_status="VERIFIED",
        source_ids=(source_id,),
    )
    question = AuthoringQuestion(
        id=uuid4(),
        stable_code="PRIMARY_DECISION",
        prompt="Which option would you choose?",
        response_type="SINGLE_CHOICE",
        response_schema={"options": ["A", "B"]},
    )
    issue = AuthoringIssue(
        id=uuid4(),
        code="PRIMARY_ISSUE",
        title="Primary decision issue",
        questions=(question,),
    )
    return AuthoringCaseVersion(
        id=uuid4(),
        case_id=case_id,
        version_no=1,
        state=ContentLifecycle.DRAFT,
        title="PostgreSQL authoring test Case",
        summary="A low-risk publication boundary test.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(issue,),
        context_blocks=(block,),
        sources=(source,),
        modifiers=("CONFIDENCE_CAPTURE",),
        is_fact_bearing=True,
    )


def _service():
    database_url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(database_url)
    repository = PostgresContentAuthoringRepository(engine)
    service = ContentAuthoringService(repository, default_authoring_registry())
    return engine, repository, service


def test_postgres_authoring_materializes_only_on_publish_and_preserves_history() -> None:
    engine, repository, service = _service()
    identity = CaseIdentity(id=uuid4(), slug=f"authoring-{uuid4().hex[:10]}")
    first_draft = _aggregate(identity.id)

    service.create_case(
        identity=identity,
        initial_version=first_draft,
        actor_ref="editor:test",
    )

    with engine.connect() as connection:
        consumer_count = connection.execute(
            text("SELECT count(*) FROM content.case_version WHERE id = :id"),
            {"id": first_draft.id},
        ).scalar_one()
    assert consumer_count == 0
    assert PostgresContextRepository(engine).get_context(first_draft.id) is None

    service.submit_for_review(first_draft.id, actor_ref="editor:test")
    service.approve(first_draft.id, actor_ref="reviewer:test")
    first = service.publish(first_draft.id, actor_ref="publisher:test")

    consumer = PostgresPerspectiveDecisionRepository(engine).get_case_version(first.id)
    assert consumer is not None
    assert consumer.primary_domain == "DAILY_LIFE"
    assert consumer.base_format == "DILEMMA"
    assert consumer.content_risk == "L0"
    assert consumer.questions[0].id == first.issues[0].questions[0].id

    first_context = PostgresContextRepository(engine).get_context(first.id)
    assert first_context is not None
    assert first_context.blocks[0].source_ids == (first.sources[0].id,)
    assert first_context.sources[0].publisher == "Example Authority"

    revision = service.create_revision(source_version_id=first.id, actor_ref="editor:2")
    assert revision.sources[0].id != first.sources[0].id
    assert revision.context_blocks[0].source_ids == (revision.sources[0].id,)

    with engine.connect() as connection:
        unpublished_count = connection.execute(
            text("SELECT count(*) FROM content.case_version WHERE id = :id"),
            {"id": revision.id},
        ).scalar_one()
    assert unpublished_count == 0

    revised = service.save_draft(
        replace(
            revision,
            title="Revised published title",
            primary_domain_code="ECONOMY_MONEY",
        )
    )
    service.submit_for_review(revised.id, actor_ref="editor:2")
    service.approve(revised.id, actor_ref="reviewer:2")
    second = service.publish(revised.id, actor_ref="publisher:2")

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT id, status, accepts_weighs, primary_domain_code
                FROM content.case_version
                WHERE case_id = :case_id
                ORDER BY version_no
                """
            ),
            {"case_id": identity.id},
        ).mappings().all()
    assert [row["status"] for row in rows] == ["SUPERSEDED", "PUBLISHED"]
    assert rows[0]["accepts_weighs"] is False
    assert rows[0]["primary_domain_code"] == "DAILY_LIFE"
    assert rows[1]["primary_domain_code"] == "ECONOMY_MONEY"

    historical = PostgresPerspectiveDecisionRepository(engine).get_case_version(first.id)
    current = PostgresPerspectiveDecisionRepository(engine).get_case_version(second.id)
    assert historical is not None and historical.primary_domain == "DAILY_LIFE"
    assert current is not None and current.primary_domain == "ECONOMY_MONEY"
    assert PostgresContextRepository(engine).get_context(first.id) is not None
    assert PostgresContextRepository(engine).get_context(second.id) is not None

    commands = [entry.command for entry in repository.list_audit(identity.id)]
    assert commands == [
        "create_case",
        "submit_for_review",
        "approve",
        "publish",
        "create_revision",
        "submit_for_review",
        "approve",
        "supersede_on_publish",
        "publish",
    ]


def test_postgres_withdraw_removes_current_consumer_visibility() -> None:
    engine, _, service = _service()
    identity = CaseIdentity(id=uuid4(), slug=f"withdraw-{uuid4().hex[:10]}")
    draft = _aggregate(identity.id)
    service.create_case(identity=identity, initial_version=draft, actor_ref="editor:test")
    service.submit_for_review(draft.id, actor_ref="editor:test")
    service.approve(draft.id, actor_ref="reviewer:test")
    published = service.publish(draft.id, actor_ref="publisher:test")

    withdrawn = service.withdraw(
        published.id,
        actor_ref="publisher:test",
        rationale="Editorial withdrawal test",
    )

    assert withdrawn.state is ContentLifecycle.WITHDRAWN
    assert withdrawn.published_at == published.published_at
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT cv.status, cv.accepts_weighs, ci.lifecycle_state
                FROM content.case_version cv
                JOIN content.case_item ci ON ci.id = cv.case_id
                WHERE cv.id = :version_id
                """
            ),
            {"version_id": published.id},
        ).mappings().one()
    assert row["status"] == "WITHDRAWN"
    assert row["accepts_weighs"] is False
    assert row["lifecycle_state"] == "WITHDRAWN"
    assert PostgresContextRepository(engine).get_context(published.id) is None
