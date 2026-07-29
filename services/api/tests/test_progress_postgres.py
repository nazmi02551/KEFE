from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def test_postgres_progress_is_actor_scoped_and_low_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    client = TestClient(create_app())

    try:
        guest = client.post("/v1/identity/guest")
        assert guest.status_code == 201
        headers = {"Authorization": f"Bearer {guest.json()['access_token']}"}

        started = client.post(
            f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
            headers=headers,
        )
        assert started.status_code == 201
        session_id = started.json()["session_id"]

        answered = client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=headers,
            json={
                "responses": [
                    {"question_id": str(DEMO_QUESTION_ID), "value": "A"},
                ]
            },
        )
        assert answered.status_code == 200

        committed = client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**headers, "Idempotency-Key": f"progress-{uuid4()}"},
        )
        assert committed.status_code == 200

        response = client.get("/v1/me/progress", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["account_offer"]["eligible"] is True
        assert body["account_offer"]["account_creation_available"] is False
        assert body["progress"]["meaningful_weigh_count"] == 1
        assert body["progress"]["distinct_case_count"] == 1
        assert body["progress"]["distinct_domain_count"] == 1
        assert len(body["progress"]["recent_cases"]) == 1

        journey = body["journey"]
        assert journey["decision_update_count"] == 0
        assert journey["revisited_case_count"] == 0
        assert journey["reflection_completion_count"] == 0
        assert journey["domain_activity"][0]["primary_domain"] == "DAILY_LIFE"
        assert journey["domain_activity"][0]["committed_weigh_count"] == 1
        assert len(journey["recent_journeys"]) == 1
        assert journey["recent_journeys"][0]["case_id"] == str(DEMO_CASE_ID)
        assert journey["recent_journeys"][0]["decision_update_count"] == 0
        assert journey["recent_journeys"][0]["reflection_completed"] is False

        serialized = response.text.lower()
        for forbidden in (
            "private_reason",
            "raw_response",
            "response_snapshot",
            "diff_snapshot",
            "personality",
            "ideology",
            "psychometric",
            "streak",
            "leaderboard",
        ):
            assert forbidden not in serialized
    finally:
        get_settings.cache_clear()
