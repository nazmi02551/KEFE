from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.consensus.in_memory import (
    DEMO_CONSENSUS_CARD_ID,
    DEMO_CONSENSUS_CARD_VERSION_ID,
)
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


def test_postgres_consensus_is_commit_gated_exposed_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    client = _client(monkeypatch)
    headers = _guest_headers(client)

    try:
        start = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
        assert start.status_code == 201
        session_id = start.json()["session_id"]

        denied = client.get(
            f"/v1/weigh-sessions/{session_id}/consensus-cards",
            headers=headers,
        )
        assert denied.status_code == 403
        assert denied.json()["code"] == "CONSENSUS_COMMIT_REQUIRED"

        answer = client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=headers,
            json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
        )
        assert answer.status_code == 200
        commit = client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**headers, "Idempotency-Key": f"postgres-consensus-{session_id}"},
        )
        assert commit.status_code == 200

        cards = client.get(
            f"/v1/weigh-sessions/{session_id}/consensus-cards",
            headers=headers,
        )
        assert cards.status_code == 200
        card = cards.json()["items"][0]
        assert card["card_id"] == str(DEMO_CONSENSUS_CARD_ID)
        assert card["card_version_id"] == str(DEMO_CONSENSUS_CARD_VERSION_ID)
        assert card["participation_state"] == "ELIGIBLE"
        assert card["aggregate"] is None

        path = (
            f"/v1/weigh-sessions/{session_id}/consensus-cards/"
            f"{DEMO_CONSENSUS_CARD_ID}/participation"
        )
        idempotency = f"postgres-consensus-participation-{session_id}"
        request = {"stance_code": "MIXED", "reason_tag_codes": ["NEED", "RULES"]}
        accepted = client.post(
            path,
            headers={**headers, "Idempotency-Key": idempotency},
            json=request,
        )
        replay = client.post(
            path,
            headers={**headers, "Idempotency-Key": idempotency},
            json=request,
        )

        assert accepted.status_code == 200
        assert replay.status_code == 200
        accepted_body = accepted.json()
        replay_body = replay.json()
        assert replay_body["participation"] == accepted_body["participation"]
        assert replay_body["participation_state"] == "PARTICIPATED"
        assert replay_body["aggregate"]["sample_size"] == accepted_body["aggregate"]["sample_size"]
        assert (
            replay_body["aggregate"]["stance_distribution"]
            == accepted_body["aggregate"]["stance_distribution"]
        )
        assert (
            replay_body["aggregate"]["reason_pattern_distribution"]
            == accepted_body["aggregate"]["reason_pattern_distribution"]
        )
        assert accepted_body["participation"]["contribution_class"] == "EXPOSED"
        assert accepted_body["aggregate"]["contribution_class"] == "EXPOSED"
        assert accepted_body["aggregate"]["sample_size"] >= 1

        engine = create_engine(database_url)
        with engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    SELECT stance_code, reason_tag_codes, contribution_class, idempotency_key
                    FROM collective.consensus_participation
                    WHERE session_id = :session_id
                      AND card_version_id = :card_version_id
                    """
                    ),
                    {
                        "session_id": session_id,
                        "card_version_id": DEMO_CONSENSUS_CARD_VERSION_ID,
                    },
                )
                .mappings()
                .one()
            )
            participation_events = (
                connection.execute(
                    text(
                        """
                    SELECT payload
                    FROM analytics.outbox_event
                    WHERE aggregate_id = :session_id
                      AND event_name = 'consensus.participated'
                    ORDER BY created_at ASC
                    """
                    ),
                    {"session_id": session_id},
                )
                .scalars()
                .all()
            )

        assert row["stance_code"] == "MIXED"
        assert row["contribution_class"] == "EXPOSED"
        assert row["idempotency_key"] == idempotency
        assert set(row["reason_tag_codes"]) == {"NEED", "RULES"}
        assert len(participation_events) == 1
        assert participation_events[0]["card_id"] == str(DEMO_CONSENSUS_CARD_ID)
        assert participation_events[0]["card_version_id"] == str(DEMO_CONSENSUS_CARD_VERSION_ID)
        assert participation_events[0]["contribution_class"] == "EXPOSED"
        assert "proposition" not in participation_events[0]
        assert "private_reason" not in participation_events[0]
    finally:
        get_settings.cache_clear()
