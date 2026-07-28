from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    AuthoringIssue,
    AuthoringQuestion,
    CaseIdentity,
    ContentLifecycle,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _draft(case_id) -> AuthoringCaseVersion:
    question = AuthoringQuestion(
        id=uuid4(),
        stable_code="PRIMARY_DECISION",
        prompt="Which option?",
        response_type="SINGLE_CHOICE",
        response_schema={"options": ["A", "B"]},
    )
    issue = AuthoringIssue(
        id=uuid4(),
        code="PRIMARY_ISSUE",
        title="Primary issue",
        questions=(question,),
    )
    return AuthoringCaseVersion(
        id=uuid4(),
        case_id=case_id,
        version_no=1,
        state=ContentLifecycle.DRAFT,
        title="PostgreSQL Flow pinned Case",
        summary="Resolved Flow provenance must survive materialization.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(issue,),
        modifiers=("CONFIDENCE_CAPTURE",),
        flow_template_code="STANDARD_COMMIT_REVEAL",
        flow_template_version_no=1,
    )


def test_postgres_publication_round_trips_flow_and_configuration_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()

    try:
        app = create_app()
        service = app.state.content_authoring_service
        repository = app.state.content_authoring_repository
        case_id = uuid4()
        draft = _draft(case_id)
        identity = CaseIdentity(
            id=case_id,
            slug=f"pg-flow-pin-{uuid4().hex[:10]}",
        )

        service.create_case(
            identity=identity,
            initial_version=draft,
            actor_ref="editor:test",
        )
        service.submit_for_review(draft.id, actor_ref="editor:test")
        service.approve(draft.id, actor_ref="reviewer:test")
        published = service.publish(draft.id, actor_ref="publisher:test")

        assert published.resolved_flow is not None
        reloaded = repository.get_version(published.id)
        assert reloaded is not None
        assert reloaded.content_configuration_id == published.content_configuration_id
        assert (
            reloaded.content_configuration_version_no
            == published.content_configuration_version_no
        )
        assert reloaded.resolved_flow == published.resolved_flow

        engine = create_engine(database_url)
        with engine.connect() as connection:
            editorial = connection.execute(
                text(
                    """
                    SELECT aggregate
                    FROM editorial.case_version
                    WHERE id = :version_id
                    """
                ),
                {"version_id": published.id},
            ).scalar_one()
            consumer = connection.execute(
                text(
                    """
                    SELECT content_configuration_id,
                           content_configuration_version_no,
                           flow_template_code,
                           flow_template_version_no,
                           resolved_flow
                    FROM content.case_version
                    WHERE id = :version_id
                    """
                ),
                {"version_id": published.id},
            ).mappings().one()

        assert editorial["content_configuration_id"] == str(
            published.content_configuration_id
        )
        assert editorial["resolved_flow"]["template_code"] == (
            "STANDARD_COMMIT_REVEAL"
        )
        assert consumer["content_configuration_id"] == (
            published.content_configuration_id
        )
        assert consumer["content_configuration_version_no"] == 1
        assert consumer["flow_template_code"] == "STANDARD_COMMIT_REVEAL"
        assert consumer["flow_template_version_no"] == 1
        assert consumer["resolved_flow"]["entry_step_code"] == "CONTEXT"

        decision_case = app.state.decision_repository.get_case_version(published.id)
        assert decision_case is not None
        assert decision_case.content_configuration_id == (
            published.content_configuration_id
        )
        assert decision_case.resolved_flow is not None
        assert decision_case.resolved_flow.template_code == "STANDARD_COMMIT_REVEAL"
    finally:
        get_settings.cache_clear()
