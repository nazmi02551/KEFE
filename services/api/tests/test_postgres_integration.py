from __future__ import annotations

import os
from uuid import uuid4

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


def test_postgres_case_weigh_commit_reveal_and_outbox(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()

    try:
        client = TestClient(create_app())
        actor_id = str(uuid4())
        actor_headers = {"X-Actor-Id": actor_id}

        case = client.get(f"/v1/cases/{DEMO_CASE_ID}")
        assert case.status_code == 200
        assert "result" not in case.json()

        start = client.post(
            f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
            headers=actor_headers,
        )
        assert start.status_code == 201
        session_id = start.json()["session_id"]

        answer = client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=actor_headers,
            json={
                "responses": [
                    {"question_id": str(DEMO_QUESTION_ID), "value": "A"},
                ]
            },
        )
        assert answer.status_code == 200

        before = client.get(
            f"/v1/weigh-sessions/{session_id}/reveal",
            headers=actor_headers,
        )
        assert before.status_code == 403

        commit = client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**actor_headers, "Idempotency-Key": f"commit-{uuid4()}"},
        )
        assert commit.status_code == 200
        assert commit.json()["state"] == "COMMITTED"

        reveal = client.get(
            f"/v1/weigh-sessions/{session_id}/reveal",
            headers=actor_headers,
        )
        assert reveal.status_code == 200
        assert reveal.json()["layer"] == "TRUSTED"

        engine = create_engine(database_url)
        with engine.connect() as connection:
            names = connection.execute(
                text(
                    """
                    SELECT event_name
                    FROM analytics.outbox_event
                    WHERE aggregate_id = :session_id
                    ORDER BY created_at
                    """
                ),
                {"session_id": session_id},
            ).scalars().all()
        assert names == ["weigh.started", "weigh.committed", "result.revealed"]
    finally:
        get_settings.cache_clear()
