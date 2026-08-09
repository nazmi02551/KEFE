from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.seed_demo import seed_demo
from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import (
    DEMO_CASE_ID,
    DEMO_CASE_VERSION_ID,
    DEMO_QUESTION_ID,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _postgres_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    return TestClient(create_app())


def _guest_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/v1/identity/guest", json={"platform": "ANDROID"})
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _start_and_answer(
    client: TestClient,
    headers: dict[str, str],
    option: str,
) -> str:
    start = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
        headers=headers,
    )
    assert start.status_code == 201
    session_id = start.json()["session_id"]
    answer = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={
            "responses": [
                {"question_id": str(DEMO_QUESTION_ID), "value": option},
            ]
        },
    )
    assert answer.status_code == 200
    return session_id


def _commit(client: TestClient, session_id: str, headers: dict[str, str]) -> None:
    response = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": f"alpha-{uuid4()}"},
    )
    assert response.status_code == 200
    assert response.json()["state"] == "COMMITTED"


def _reveal(client: TestClient, session_id: str, headers: dict[str, str]):
    response = client.get(
        f"/v1/weigh-sessions/{session_id}/reveal",
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def test_live_raw_result_counts_only_committed_actors_and_trusted_still_wins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(database_url)

    # The canonical demo seed intentionally carries a static TRUSTED snapshot. Remove only that
    # snapshot for this bounded test so the Connected Alpha RAW fallback can be exercised. The
    # fixture is restored in finally even if an assertion fails.
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DELETE FROM analytics.result_snapshot
                WHERE case_version_id = :case_version_id
                  AND layer = 'TRUSTED'
                """
            ),
            {"case_version_id": DEMO_CASE_VERSION_ID},
        )

    client = _postgres_client(monkeypatch)
    try:
        baseline = client.app.state.decision_repository.get_reveal(DEMO_CASE_VERSION_ID)
        baseline_n = 0 if baseline is None else baseline.n
        if baseline is not None:
            assert baseline.layer == "RAW"
            assert baseline.confidence == "INSUFFICIENT"

        first_headers = _guest_headers(client)
        second_headers = _guest_headers(client)
        first_session = _start_and_answer(client, first_headers, "A")
        second_session = _start_and_answer(client, second_headers, "B")

        # Second actor is still DRAFT: only the first committed actor may enter the aggregate.
        _commit(client, first_session, first_headers)
        first_reveal = _reveal(client, first_session, first_headers)
        assert first_reveal["layer"] == "RAW"
        assert first_reveal["confidence"] == "INSUFFICIENT"
        assert first_reveal["n"] == baseline_n + 1
        assert set(first_reveal["result"]) == {"A", "B"}
        assert sum(first_reveal["result"].values()) == pytest.approx(1.0)

        still_one = client.app.state.decision_repository.get_reveal(DEMO_CASE_VERSION_ID)
        assert still_one is not None
        assert still_one.n == baseline_n + 1

        _commit(client, second_session, second_headers)
        second_reveal = _reveal(client, second_session, second_headers)
        assert second_reveal["layer"] == "RAW"
        assert second_reveal["n"] == baseline_n + 2
        assert sum(second_reveal["result"].values()) == pytest.approx(1.0)

        reread_first = _reveal(client, first_session, first_headers)
        assert reread_first["layer"] == "RAW"
        assert reread_first["n"] == baseline_n + 2

        # Reintroducing a reviewed TRUSTED snapshot must preserve the existing precedence policy.
        seed_demo()
        trusted = _reveal(client, first_session, first_headers)
        assert trusted["layer"] == "TRUSTED"
    finally:
        seed_demo()
        get_settings.cache_clear()
        engine.dispose()
