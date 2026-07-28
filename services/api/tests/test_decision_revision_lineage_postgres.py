from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

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
        title="Decision revision lineage Case",
        summary="Initial principle, Context exposure and final retest.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(issue,),
        flow_template_code="PRINCIPLE_CONTEXT_RETEST",
        flow_template_version_no=1,
    )


def test_postgres_principle_context_retest_persists_revision_delta_lineage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()

    try:
        app = create_app()
        authoring = app.state.content_authoring_service
        case_id = uuid4()
        draft = _draft(case_id)
        authoring.create_case(
            identity=CaseIdentity(
                id=case_id,
                slug=f"decision-lineage-{uuid4().hex[:10]}",
            ),
            initial_version=draft,
            actor_ref="editor:test",
        )
        authoring.submit_for_review(draft.id, actor_ref="editor:test")
        authoring.approve(draft.id, actor_ref="reviewer:test")
        published = authoring.publish(draft.id, actor_ref="publisher:test")
        question_id = published.issues[0].questions[0].id

        client = TestClient(app)
        guest = client.post("/v1/identity/guest")
        assert guest.status_code == 201
        headers = {"Authorization": f"Bearer {guest.json()['access_token']}"}

        started = client.post(
            f"/v1/cases/{case_id}/weigh-sessions",
            headers=headers,
        )
        assert started.status_code == 201
        session_id = started.json()["session_id"]

        initial_response = client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=headers,
            json={"responses": [{"question_id": str(question_id), "value": "A"}]},
        )
        assert initial_response.status_code == 200

        initial_commit = client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**headers, "Idempotency-Key": f"initial-{uuid4().hex}"},
        )
        assert initial_commit.status_code == 200

        after_initial = client.get(
            f"/v1/weigh-sessions/{session_id}/flow",
            headers=headers,
        )
        assert after_initial.status_code == 200
        assert [item["state"] for item in after_initial.json()["steps"]] == [
            "COMPLETED",
            "READY",
            "BLOCKED",
            "BLOCKED",
        ]

        exposure = client.post(
            f"/v1/weigh-sessions/{session_id}/flow-steps/CONTEXT/exposures",
            headers={**headers, "Idempotency-Key": f"context-{uuid4().hex}"},
        )
        assert exposure.status_code == 201
        assert exposure.json()["resource_category"] == "CONTEXT"
        assert exposure.json()["intervention_id"] is not None

        after_context = client.get(
            f"/v1/weigh-sessions/{session_id}/flow",
            headers=headers,
        )
        assert [item["state"] for item in after_context.json()["steps"]] == [
            "COMPLETED",
            "COMPLETED",
            "READY",
            "BLOCKED",
        ]

        revised = client.put(
            f"/v1/weigh-sessions/{session_id}/decision-steps/FINAL_DECISION/responses",
            headers=headers,
            json={"responses": [{"question_id": str(question_id), "value": "B"}]},
        )
        assert revised.status_code == 200
        assert revised.json()["response_count"] == 1

        revision_commit = client.post(
            f"/v1/weigh-sessions/{session_id}/decision-steps/FINAL_DECISION/commit",
            headers={**headers, "Idempotency-Key": f"revision-{uuid4().hex}"},
        )
        assert revision_commit.status_code == 200
        assert revision_commit.json()["revision_no"] == 2
        assert revision_commit.json()["delta_id"] is not None

        lineage = client.get(
            f"/v1/weigh-sessions/{session_id}/lineage",
            headers=headers,
        )
        assert lineage.status_code == 200
        body = lineage.json()
        assert [item["flow_step_code"] for item in body["revisions"]] == [
            "PRINCIPLE",
            "FINAL_DECISION",
        ]
        assert [item["contribution_class"] for item in body["revisions"]] == [
            "CORE_PRE_RESULT",
            "CORE_PRE_RESULT",
        ]
        assert len(body["exposures"]) == 1
        assert len(body["interventions"]) == 1
        assert len(body["deltas"]) == 1
        assert body["deltas"][0]["changed_question_ids"] == [str(question_id)]
        assert body["deltas"][0]["changed_count"] == 1

        final_flow = client.get(
            f"/v1/weigh-sessions/{session_id}/flow",
            headers=headers,
        )
        assert [item["state"] for item in final_flow.json()["steps"]] == [
            "COMPLETED",
            "COMPLETED",
            "COMPLETED",
            "UNSUPPORTED",
        ]
        assert final_flow.json()["steps"][-1]["reason_code"] == (
            "FLOW_REFLECTION_RUNTIME_PENDING"
        )
    finally:
        get_settings.cache_clear()
