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


def test_postgres_private_reason_is_private_pending_and_commit_immutable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    client = _client(monkeypatch)
    headers = _guest_headers(client)

    try:
        start = client.post(
            f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
            headers=headers,
        )
        assert start.status_code == 201
        session_id = start.json()["session_id"]

        saved = client.put(
            f"/v1/weigh-sessions/{session_id}/reason",
            headers=headers,
            json={
                "tags": ["FAIRNESS", "NEED"],
                "text": "Bu kararın daha adil olduğunu düşündüm.",
            },
        )
        assert saved.status_code == 200
        assert saved.json()["visibility"] == "PRIVATE"
        assert saved.json()["moderation_state"] == "PENDING"

        engine = create_engine(database_url)
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT tags, text_body, moderation_state, visibility
                    FROM decision.private_reason
                    WHERE session_id = :session_id
                    """
                ),
                {"session_id": session_id},
            ).mappings().one()
        assert row["tags"] == ["FAIRNESS", "NEED"]
        assert row["text_body"] == "Bu kararın daha adil olduğunu düşündüm."
        assert row["moderation_state"] == "PENDING"
        assert row["visibility"] == "PRIVATE"

        answer = client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=headers,
            json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
        )
        assert answer.status_code == 200
        commit = client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**headers, "Idempotency-Key": "postgres-reason-commit"},
        )
        assert commit.status_code == 200

        blocked = client.put(
            f"/v1/weigh-sessions/{session_id}/reason",
            headers=headers,
            json={"tags": ["RESPONSIBILITY"]},
        )
        assert blocked.status_code == 409
        assert blocked.json()["code"] == "WEIGH_SESSION_NOT_EDITABLE"
    finally:
        get_settings.cache_clear()
