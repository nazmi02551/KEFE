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
        summary="Initial principle, Context exposure, final retest and Reflection.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(issue,),
        flow_template_code="PRINCIPLE_CONTEXT_RETEST",
        flow_template_version_no=1,
    )


def test_postgres_principle_context_retest_persists_revision_delta_and_reflection(
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

        exposure = client.post(
            f"/v1/weigh-sessions/{session_id}/flow-steps/CONTEXT/exposures",
            headers={**headers, "Idempotency-Key": f"context-{uuid4().hex}"},
        )
        assert exposure.status_code == 201
        assert exposure.json()["intervention_id"] is not None

        revised = client.put(
            f"/v1/weigh-sessions/{session_id}/decision-steps/FINAL_DECISION/responses",
            headers=headers,
            json={"responses": [{"question_id": str(question_id), "value": "B"}]},
        )
        assert revised.status_code == 200

        revision_commit = client.post(
            f"/v1/weigh-sessions/{session_id}/decision-steps/FINAL_DECISION/commit",
            headers={**headers, "Idempotency-Key": f"revision-{uuid4().hex}"},
        )
        assert revision_commit.status_code == 200
        assert revision_commit.json()["revision_no"] == 2
        assert revision_commit.json()["delta_id"] is not None

        reflection_flow = client.get(
            f"/v1/weigh-sessions/{session_id}/flow",
            headers=headers,
        )
        assert [item["state"] for item in reflection_flow.json()["steps"]] == [
            "COMPLETED",
            "COMPLETED",
            "COMPLETED",
            "READY",
        ]
        assert reflection_flow.json()["execution_support"] == "FULL"

        reflection = client.get(
            f"/v1/weigh-sessions/{session_id}/reflection-steps/REFLECTION",
            headers=headers,
        )
        assert reflection.status_code == 200
        reflection_body = reflection.json()
        assert reflection_body["revision_count"] == 2
        assert reflection_body["decision_changed"] is True
        assert reflection_body["changed_question_count"] == 1
        assert reflection_body["intervention_count"] == 1
        assert reflection_body["intervention_type_codes"] == ["CONTEXT_REVEAL"]
        assert reflection_body["completed"] is False
        assert "responses" not in reflection_body
        assert "private_reason" not in reflection_body

        completion_key = f"reflection-{uuid4().hex}"
        completed = client.post(
            f"/v1/weigh-sessions/{session_id}/reflection-steps/REFLECTION/complete",
            headers={**headers, "Idempotency-Key": completion_key},
        )
        assert completed.status_code == 200
        replay = client.post(
            f"/v1/weigh-sessions/{session_id}/reflection-steps/REFLECTION/complete",
            headers={**headers, "Idempotency-Key": completion_key},
        )
        assert replay.status_code == 200
        assert replay.json()["reflection_completion_id"] == completed.json()[
            "reflection_completion_id"
        ]

        final_flow = client.get(
            f"/v1/weigh-sessions/{session_id}/flow",
            headers=headers,
        )
        assert final_flow.json()["steps"][-1]["state"] == "COMPLETED"

        lineage = client.get(
            f"/v1/weigh-sessions/{session_id}/lineage",
            headers=headers,
        )
        assert lineage.status_code == 200
        body = lineage.json()
        assert len(body["revisions"]) == 2
        assert len(body["exposures"]) == 1
        assert len(body["interventions"]) == 1
        assert len(body["deltas"]) == 1
        assert body["deltas"][0]["changed_count"] == 1

        progress = client.get("/v1/me/progress", headers=headers)
        assert progress.status_code == 200
        journey = progress.json()["journey"]
        assert journey["decision_update_count"] == 1
        assert journey["revisited_case_count"] == 1
        assert journey["reflection_completion_count"] == 1
        assert journey["domain_activity"] == [
            {
                "primary_domain": "DAILY_LIFE",
                "committed_weigh_count": 1,
                "last_committed_at": progress.json()["progress"]["last_committed_at"],
            }
        ]
        assert len(journey["recent_journeys"]) == 1
        recent = journey["recent_journeys"][0]
        assert recent["case_id"] == str(case_id)
        assert recent["decision_update_count"] == 1
        assert recent["reflection_completed"] is True
        assert recent["latest_decision_at"] > recent["initial_committed_at"]
        report = progress.json()["personal_report"]
        assert [item["type"] for item in report["moments"]] == [
            "REFLECTION_COMPLETED",
            "DECISION_UPDATE",
            "INITIAL_COMMIT",
        ]
        assert report["moments"][0]["revision_no"] is None
        assert report["moments"][1]["revision_no"] == 2
        assert report["moments"][2]["revision_no"] is None
        assert all(item["case_id"] == str(case_id) for item in report["moments"])
        assert all(
            item["case_version_id"] == str(published.id)
            for item in report["moments"]
        )
        serialized = progress.text.lower()
        for forbidden in (
            "response_snapshot",
            "private_reason",
            "diff_snapshot",
            "exposure_metadata",
            "intervention_metadata",
            "personality",
            "ideology",
            "psychometric",
            "session_id",
            "revision_id",
            "reflection_completion_id",
        ):
            assert forbidden not in serialized
    finally:
        get_settings.cache_clear()
