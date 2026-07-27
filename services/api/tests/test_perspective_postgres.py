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


def _client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    return TestClient(create_app())


def _guest_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_postgres_perspective_is_commit_gated_and_opposing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(monkeypatch)
    headers = _guest_headers(client)
    try:
        start = client.post(
            f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
            headers=headers,
        )
        assert start.status_code == 201
        session_id = start.json()["session_id"]

        blocked = client.get(
            f"/v1/weigh-sessions/{session_id}/perspectives",
            headers=headers,
        )
        assert blocked.status_code == 403
        assert blocked.json()["code"] == "PERSPECTIVE_COMMIT_REQUIRED"

        answer = client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=headers,
            json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
        )
        assert answer.status_code == 200
        commit = client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**headers, "Idempotency-Key": f"perspective-{uuid4()}"},
        )
        assert commit.status_code == 200

        perspective = client.get(
            f"/v1/weigh-sessions/{session_id}/perspectives",
            headers=headers,
        )
        assert perspective.status_code == 200
        body = perspective.json()
        assert body["selection_policy"] == "EDITORIAL_OPPOSITION_V1"
        assert body["viewer_value"] == "A"
        assert body["items"]
        assert all(item["target_value"] != "A" for item in body["items"])
        assert all(item["source_kind"] == "EDITORIAL_HUMAN" for item in body["items"])
        assert all(item["moderation_state"] == "ALLOWED" for item in body["items"])
    finally:
        get_settings.cache_clear()
