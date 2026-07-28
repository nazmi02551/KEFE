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
        title="Generic Flow runtime Case",
        summary="End-to-end pinned Flow runtime fixture.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(issue,),
        modifiers=("CONFIDENCE_CAPTURE",),
        flow_template_code="STANDARD_COMMIT_REVEAL",
        flow_template_version_no=1,
    )


def test_postgres_flow_runtime_http_tracks_server_commit_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()

    try:
        app = create_app()
        authoring = app.state.content_authoring_service
        case_id = uuid4()
        draft = _draft(case_id)
        identity = CaseIdentity(
            id=case_id,
            slug=f"flow-runtime-{uuid4().hex[:10]}",
        )
        authoring.create_case(
            identity=identity,
            initial_version=draft,
            actor_ref="editor:test",
        )
        authoring.submit_for_review(draft.id, actor_ref="editor:test")
        authoring.approve(draft.id, actor_ref="reviewer:test")
        published = authoring.publish(draft.id, actor_ref="publisher:test")

        client = TestClient(app)
        guest = client.post("/v1/identity/guest")
        assert guest.status_code == 201
        headers = {
            "Authorization": f"Bearer {guest.json()['access_token']}",
        }

        started = client.post(
            f"/v1/cases/{case_id}/weigh-sessions",
            headers=headers,
        )
        assert started.status_code == 201
        session_id = started.json()["session_id"]

        before = client.get(
            f"/v1/weigh-sessions/{session_id}/flow",
            headers=headers,
        )
        assert before.status_code == 200
        before_body = before.json()
        assert before_body["case_version_id"] == str(published.id)
        assert before_body["execution_support"] == "FULL"
        assert [item["state"] for item in before_body["steps"]] == [
            "READY",
            "READY",
            "BLOCKED",
        ]
        assert before_body["steps"][2]["reason_code"] == "FLOW_COMMIT_REQUIRED"
        assert "result" not in before_body

        response = client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=headers,
            json={
                "responses": [
                    {
                        "question_id": str(published.issues[0].questions[0].id),
                        "value": "A",
                    }
                ]
            },
        )
        assert response.status_code == 200

        committed = client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**headers, "Idempotency-Key": f"flow-{uuid4().hex}"},
        )
        assert committed.status_code == 200

        after = client.get(
            f"/v1/weigh-sessions/{session_id}/flow",
            headers=headers,
        )
        assert after.status_code == 200
        assert [item["state"] for item in after.json()["steps"]] == [
            "READY",
            "COMPLETED",
            "READY",
        ]
    finally:
        get_settings.cache_clear()
