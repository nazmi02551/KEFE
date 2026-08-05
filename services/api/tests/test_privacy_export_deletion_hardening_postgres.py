from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)

EXPECTED_ACTOR_FOREIGN_KEYS = {
    ("collective", "consensus_participation", "actor_id"),
    ("community", "reason", "actor_id"),
    ("community", "reason_reaction", "actor_id"),
    ("community", "reason_report", "reporter_actor_id"),
    ("decision", "decision_revision", "actor_id"),
    ("decision", "exposure", "actor_id"),
    ("decision", "reflection_completion", "actor_id"),
    ("decision", "weigh_session", "actor_id"),
    ("decision", "weigh_session", "merged_from_actor_id"),
    ("identity", "account_identifier", "actor_id"),
    ("identity", "actor_merge", "account_actor_id"),
    ("identity", "actor_merge", "guest_actor_id"),
    ("identity", "actor_session", "actor_id"),
    ("sharing", "share_record", "actor_id"),
}


def _app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    app = create_app()
    return app, TestClient(app)


def _guest(client: TestClient) -> tuple[dict[str, str], UUID]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    return (
        {"Authorization": f"Bearer {response.json()['access_token']}"},
        UUID(response.json()["actor_id"]),
    )


def _commit(client: TestClient, headers: dict[str, str]) -> str:
    start = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    assert start.status_code == 201
    session_id = start.json()["session_id"]
    assert (
        client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=headers,
            json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**headers, "Idempotency-Key": f"privacy-pg-{session_id}"},
        ).status_code
        == 200
    )
    return session_id


def test_postgres_export_restart_and_concurrent_one_receipt_deletion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    app, client = _app(monkeypatch)
    headers, actor_id = _guest(client)
    _commit(client, headers)

    first = client.get("/v1/me/privacy-export", headers=headers)
    assert first.status_code == 200
    first_body = first.json()

    second_app = create_app()
    second_client = TestClient(second_app)
    second = second_client.get("/v1/me/privacy-export", headers=headers)
    assert second.status_code == 200
    assert second.json()["data_sha256"] == first_body["data_sha256"]
    assert second.json()["manifest"] == first_body["manifest"]

    engine = create_engine(database_url)
    linked_guest = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO identity.actor (id, actor_kind, state) VALUES (:id, 'GUEST', 'ACTIVE')"
            ),
            {"id": linked_guest},
        )
        connection.execute(
            text(
                """
                INSERT INTO identity.actor_merge (guest_actor_id, account_actor_id, merged_at)
                VALUES (:guest_actor_id, :account_actor_id, now())
                """
            ),
            {"guest_actor_id": linked_guest, "account_actor_id": actor_id},
        )

    repository = second_app.state.privacy_repository
    deleted_times = [
        datetime(2026, 8, 5, 10, 0, tzinfo=UTC),
        datetime(2026, 8, 5, 10, 1, tzinfo=UTC),
    ]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                repository.delete_actor_data,
                actor_id=actor_id,
                actor_kind="GUEST",
                deleted_at=deleted_at,
            )
            for deleted_at in deleted_times
        ]
    receipts = [future.result() for future in futures]
    assert receipts[0] == receipts[1]
    assert receipts[0].policy_version == "PRIVACY_SELF_SERVICE_V2"

    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM privacy.actor_deletion_receipt WHERE actor_id = :actor_id"
                ),
                {"actor_id": actor_id},
            ).scalar_one()
            == 1
        )
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM identity.actor_merge "
                    "WHERE guest_actor_id = :actor_id OR account_actor_id = :actor_id"
                ),
                {"actor_id": actor_id},
            ).scalar_one()
            == 0
        )
        assert (
            connection.execute(
                text("SELECT state FROM identity.actor WHERE id = :actor_id"),
                {"actor_id": actor_id},
            ).scalar_one()
            == "DELETED"
        )

    third_app = create_app()
    replay = third_app.state.privacy_repository.delete_actor_data(
        actor_id=actor_id,
        actor_kind="GUEST",
        deleted_at=datetime(2026, 8, 5, 11, 0, tzinfo=UTC),
    )
    assert replay == receipts[0]

    with pytest.raises(DBAPIError), engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE privacy.actor_deletion_receipt "
                "SET policy_version = 'MUTATED' WHERE actor_id = :actor_id"
            ),
            {"actor_id": actor_id},
        )
    with pytest.raises(DBAPIError), engine.begin() as connection:
        connection.execute(
            text("DELETE FROM privacy.actor_deletion_receipt WHERE actor_id = :actor_id"),
            {"actor_id": actor_id},
        )
    get_settings.cache_clear()


def test_postgres_actor_reference_catalog_is_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    _app(monkeypatch)
    engine = create_engine(database_url)
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT tc.table_schema, tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.constraint_schema = kcu.constraint_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON tc.constraint_name = ccu.constraint_name
                 AND tc.constraint_schema = ccu.constraint_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND ccu.table_schema = 'identity'
                  AND ccu.table_name = 'actor'
                ORDER BY tc.table_schema, tc.table_name, kcu.column_name
                """
            )
        ).all()
    assert {tuple(row) for row in rows} == EXPECTED_ACTOR_FOREIGN_KEYS
    get_settings.cache_clear()
