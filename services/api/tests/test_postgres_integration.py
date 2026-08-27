from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
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


def _postgres_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    return TestClient(create_app())


def _guest_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _start_and_answer(client: TestClient, actor_headers: dict[str, str]) -> str:
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
    return session_id


def test_postgres_explore_lists_published_cases(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _postgres_client(monkeypatch)
    try:
        response = client.get("/v1/cases?limit=10")
        assert response.status_code == 200
        items = response.json()["items"]
        assert any(item["case_id"] == str(DEMO_CASE_ID) for item in items)
        assert all("questions" not in item for item in items)
        assert all(type(item["is_real_event"]) is bool for item in items)
    finally:
        get_settings.cache_clear()


def test_postgres_case_weigh_commit_reveal_and_outbox(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    client = _postgres_client(monkeypatch)
    actor_headers = _guest_headers(client)

    try:
        case = client.get(f"/v1/cases/{DEMO_CASE_ID}")
        assert case.status_code == 200
        assert "result" not in case.json()

        session_id = _start_and_answer(client, actor_headers)

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
        assert names == [
            "weigh.started",
            "weigh.committed",
            "result.revealed",
            "exposure.recorded",
        ]
    finally:
        get_settings.cache_clear()


def test_competing_postgres_commits_create_one_commit_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    client = _postgres_client(monkeypatch)
    actor_headers = _guest_headers(client)

    try:
        session_id = _start_and_answer(client, actor_headers)

        def commit(key: str) -> tuple[int, str | None]:
            with TestClient(client.app) as worker_client:
                response = worker_client.post(
                    f"/v1/weigh-sessions/{session_id}/commit",
                    headers={**actor_headers, "Idempotency-Key": key},
                )
                return response.status_code, response.json().get("code")

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(commit, ("race-key-a", "race-key-b")))

        assert sorted(status for status, _ in outcomes) == [200, 409]
        assert {code for _, code in outcomes if code} == {"WEIGH_SESSION_ALREADY_COMMITTED"}

        engine = create_engine(database_url)
        with engine.connect() as connection:
            commit_events = connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM analytics.outbox_event
                    WHERE aggregate_id = :session_id
                      AND event_name = 'weigh.committed'
                    """
                ),
                {"session_id": session_id},
            ).scalar_one()
        assert commit_events == 1
    finally:
        get_settings.cache_clear()


def test_concurrent_same_key_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _postgres_client(monkeypatch)
    actor_headers = _guest_headers(client)

    try:
        session_id = _start_and_answer(client, actor_headers)
        shared_key = f"same-key-{uuid4()}"

        def commit() -> tuple[int, str | None]:
            with TestClient(client.app) as worker_client:
                response = worker_client.post(
                    f"/v1/weigh-sessions/{session_id}/commit",
                    headers={**actor_headers, "Idempotency-Key": shared_key},
                )
                return response.status_code, response.json().get("committed_at")

        with ThreadPoolExecutor(max_workers=2) as executor:
            first, second = executor.map(lambda _: commit(), range(2))

        assert first[0] == 200
        assert second[0] == 200
        assert first[1] == second[1]
    finally:
        get_settings.cache_clear()


def test_guest_token_is_persisted_and_revocable(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _postgres_client(monkeypatch)
    headers = _guest_headers(client)

    try:
        assert client.post(
            f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
            headers=headers,
        ).status_code == 201

        revoked = client.delete("/v1/identity/session", headers=headers)
        assert revoked.status_code == 204

        denied = client.post(
            f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
            headers=headers,
        )
        assert denied.status_code == 401
        assert denied.json()["code"] == "AUTH_TOKEN_REVOKED"
    finally:
        get_settings.cache_clear()
