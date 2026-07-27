from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    return TestClient(create_app())


def _guest_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_postgres_perspective_is_commit_gated_curated_and_private_reason_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    client = _client(monkeypatch)
    headers = _guest_headers(client)
    private_text = "postgres özel gerekçe görünmemeli"

    try:
        start = client.post(
            f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
            headers=headers,
        )
        assert start.status_code == 201
        session_id = start.json()["session_id"]

        denied = client.get(
            f"/v1/weigh-sessions/{session_id}/perspectives",
            headers=headers,
        )
        assert denied.status_code == 403
        assert denied.json()["code"] == "RESULT_COMMIT_REQUIRED"

        reason = client.put(
            f"/v1/weigh-sessions/{session_id}/reason",
            headers=headers,
            json={"tags": ["FAIRNESS"], "text": private_text},
        )
        assert reason.status_code == 200
        answer = client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=headers,
            json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
        )
        assert answer.status_code == 200
        commit = client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**headers, "Idempotency-Key": "postgres-perspective-commit"},
        )
        assert commit.status_code == 200

        response = client.get(
            f"/v1/weigh-sessions/{session_id}/perspectives",
            headers=headers,
        )
        assert response.status_code == 200
        body = response.json()
        assert body["methodology"]["mode"] == "DEGRADED_CURATED"
        assert body["methodology"]["sample_size"] == 4
        assert [card["slot"] for card in body["cards"]] == [
            "NEAR",
            "OPPOSING",
            "BRIDGE",
            "ALTERNATIVE_CONTEXT",
        ]
        assert private_text not in response.text

        engine = create_engine(database_url)
        with engine.connect() as connection:
            event_payload = connection.execute(
                text(
                    """
                    SELECT payload
                    FROM analytics.outbox_event
                    WHERE aggregate_id = :session_id
                      AND event_name = 'perspective.viewed'
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                ),
                {"session_id": session_id},
            ).scalar_one()
        assert event_payload == {
            "case_version_id": body["case_version_id"],
            "mode": "DEGRADED_CURATED",
            "card_count": 4,
        }
        assert private_text not in str(event_payload)
    finally:
        get_settings.cache_clear()
