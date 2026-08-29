from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.analytics.models import (
    AnalyticsEvent,
    AnalyticsPrivacyClass,
    AnalyticsRetentionClass,
)
from kefe_api.modules.decision.bootstrap import (
    DEMO_CASE_ID,
    DEMO_CASE_VERSION_ID,
    DEMO_QUESTION_ID,
)

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
    ("identity", "guest_merge_replay", "account_actor_id"),
    ("identity", "guest_merge_replay", "merged_from_actor_id"),
    ("identity", "guest_merge_replay", "source_actor_id"),
    ("sharing", "share_record", "actor_id"),
}
EXPECTED_RETAINED_ANALYTICS_ACTOR_COLUMNS = {
    ("analytics_event", "actor_id", "YES", "uuid"),
    ("activation_journey", "actor_id", "YES", "uuid"),
}


def _analytics_event(*, actor_id: UUID, session_id: UUID) -> AnalyticsEvent:
    return AnalyticsEvent(
        id=uuid4(),
        source_event_id=uuid4(),
        source_event_name="weigh.started",
        source_event_version=1,
        analytics_name="activation.weigh_started",
        analytics_version=1,
        occurred_at=datetime(2026, 8, 29, 8, 0, tzinfo=UTC),
        producer_version="privacy-deletion-postgres-test",
        actor_id=actor_id,
        session_id=session_id,
        case_version_id=DEMO_CASE_VERSION_ID,
        contribution_class=None,
        privacy_class=AnalyticsPrivacyClass.PRODUCT_ANALYTICS,
        retention_class=AnalyticsRetentionClass.STANDARD_13_MONTHS,
        metric_families=("ACTIVATION",),
        payload={},
    )


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
    session_id = UUID(_commit(client, headers))
    analytics_event = _analytics_event(actor_id=actor_id, session_id=session_id)
    assert app.state.analytics_event_store.append_once(analytics_event) is True

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
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM analytics.analytics_event "
                    "WHERE id = :event_id AND actor_id IS NULL"
                ),
                {"event_id": analytics_event.id},
            ).scalar_one()
            == 1
        )
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM analytics.activation_journey "
                    "WHERE session_id = :session_id AND actor_id IS NULL"
                ),
                {"session_id": session_id},
            ).scalar_one()
            == 1
        )

    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE analytics.analytics_event SET actor_id = :actor_id "
                "WHERE id = :event_id"
            ),
            {"actor_id": actor_id, "event_id": analytics_event.id},
        )
        connection.execute(
            text(
                "UPDATE analytics.activation_journey SET actor_id = :actor_id "
                "WHERE session_id = :session_id"
            ),
            {"actor_id": actor_id, "session_id": session_id},
        )

    third_app = create_app()
    replay = third_app.state.privacy_repository.delete_actor_data(
        actor_id=actor_id,
        actor_kind="GUEST",
        deleted_at=datetime(2026, 8, 5, 11, 0, tzinfo=UTC),
    )
    assert replay == receipts[0]

    with engine.connect() as connection:
        assert (
            connection.execute(
                text(
                    "SELECT actor_id FROM analytics.analytics_event "
                    "WHERE id = :event_id"
                ),
                {"event_id": analytics_event.id},
            ).scalar_one_or_none()
            is None
        )
        assert (
            connection.execute(
                text(
                    "SELECT actor_id FROM analytics.activation_journey "
                    "WHERE session_id = :session_id"
                ),
                {"session_id": session_id},
            ).scalar_one_or_none()
            is None
        )

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


def test_postgres_retained_analytics_actor_column_catalog_is_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    _app(monkeypatch)
    engine = create_engine(database_url)
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT table_name, column_name, is_nullable, data_type
                FROM information_schema.columns
                WHERE table_schema = 'analytics'
                  AND column_name = 'actor_id'
                ORDER BY table_name, column_name
                """
            )
        ).all()
    assert {tuple(row) for row in rows} == EXPECTED_RETAINED_ANALYTICS_ACTOR_COLUMNS
    get_settings.cache_clear()


def test_postgres_0040_backfills_preexisting_deleted_actor_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    _app(monkeypatch)
    engine = create_engine(database_url)
    actor_id = uuid4()
    session_id = uuid4()
    event_id = uuid4()
    source_event_id = uuid4()
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

    command.downgrade(config, "20260829_0039")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO identity.actor (id, actor_kind, state) "
                    "VALUES (:actor_id, 'GUEST', 'DELETED')"
                ),
                {"actor_id": actor_id},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO analytics.analytics_event (
                        id, source_event_id, source_event_name, source_event_version,
                        analytics_name, analytics_version, occurred_at, producer_version,
                        actor_id, session_id, case_version_id, contribution_class,
                        privacy_class, retention_class, metric_families, payload
                    ) VALUES (
                        :event_id, :source_event_id, 'weigh.started', 1,
                        'activation.weigh_started', 1, :occurred_at, '0040-backfill-test',
                        :actor_id, :session_id, :case_version_id, NULL,
                        'PRODUCT_ANALYTICS', 'STANDARD_13_MONTHS', '[]'::jsonb, '{}'::jsonb
                    )
                    """
                ),
                {
                    "event_id": event_id,
                    "source_event_id": source_event_id,
                    "occurred_at": datetime(2026, 8, 29, 8, 0, tzinfo=UTC),
                    "actor_id": actor_id,
                    "session_id": session_id,
                    "case_version_id": DEMO_CASE_VERSION_ID,
                },
            )
            connection.execute(
                text(
                    """
                    INSERT INTO analytics.activation_journey (
                        session_id, actor_id, case_version_id,
                        started_at, started_source_event_id
                    ) VALUES (
                        :session_id, :actor_id, :case_version_id,
                        :started_at, :source_event_id
                    )
                    """
                ),
                {
                    "session_id": session_id,
                    "actor_id": actor_id,
                    "case_version_id": DEMO_CASE_VERSION_ID,
                    "started_at": datetime(2026, 8, 29, 8, 0, tzinfo=UTC),
                    "source_event_id": source_event_id,
                },
            )

        command.upgrade(config, "head")

        with engine.connect() as connection:
            event = connection.execute(
                text(
                    "SELECT actor_id, session_id, case_version_id "
                    "FROM analytics.analytics_event WHERE id = :event_id"
                ),
                {"event_id": event_id},
            ).one()
            journey = connection.execute(
                text(
                    "SELECT actor_id, session_id, case_version_id, started_source_event_id "
                    "FROM analytics.activation_journey WHERE session_id = :session_id"
                ),
                {"session_id": session_id},
            ).one()
        assert tuple(event) == (None, session_id, DEMO_CASE_VERSION_ID)
        assert tuple(journey) == (
            None,
            session_id,
            DEMO_CASE_VERSION_ID,
            source_event_id,
        )
    finally:
        command.upgrade(config, "head")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM analytics.activation_journey "
                    "WHERE session_id = :session_id"
                ),
                {"session_id": session_id},
            )
            connection.execute(
                text("DELETE FROM analytics.analytics_event WHERE id = :event_id"),
                {"event_id": event_id},
            )
            connection.execute(
                text("DELETE FROM identity.actor WHERE id = :actor_id"),
                {"actor_id": actor_id},
            )
        engine.dispose()
        get_settings.cache_clear()
