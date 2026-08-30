from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_outbox import PostgresOutboxStore

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


@pytest.fixture(autouse=True)
def _isolated_outbox() -> Iterator[None]:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM analytics.outbox_event"))
    yield
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM analytics.outbox_event"))


def _insert_event(database_url: str) -> str:
    event_id = str(uuid4())
    aggregate_id = str(uuid4())
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO analytics.outbox_event (
                    id,
                    aggregate_type,
                    aggregate_id,
                    event_name,
                    event_version,
                    occurred_at,
                    payload
                )
                VALUES (
                    :id,
                    'WEIGH_SESSION',
                    :aggregate_id,
                    'test.outbox',
                    1,
                    now(),
                    '{}'::jsonb
                )
                """
            ),
            {"id": event_id, "aggregate_id": aggregate_id},
        )
    return event_id


def test_outbox_claim_lease_retry_and_publish() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(database_url)
    store = PostgresOutboxStore(engine)
    event_id = _insert_event(database_url)

    first = store.claim_batch(worker_id="worker-a", limit=10, lease_seconds=30)
    claimed = next(event for event in first if str(event.id) == event_id)
    assert claimed.attempts == 1

    second = store.claim_batch(worker_id="worker-b", limit=10, lease_seconds=30)
    assert all(str(event.id) != event_id for event in second)

    store.mark_failed(
        event_id=claimed.id,
        worker_id="worker-a",
        error="provider unavailable",
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=1),
        dead_letter=False,
    )

    third = store.claim_batch(worker_id="worker-b", limit=10, lease_seconds=30)
    reclaimed = next(event for event in third if str(event.id) == event_id)
    assert reclaimed.attempts == 2

    store.mark_published(event_id=reclaimed.id, worker_id="worker-b")

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT published_at, attempts, last_error, lock_owner, locked_until
                FROM analytics.outbox_event
                WHERE id = :event_id
                """
            ),
            {"event_id": event_id},
        ).mappings().one()

    assert row["published_at"] is not None
    assert row["attempts"] == 2
    assert row["last_error"] is None
    assert row["lock_owner"] is None
    assert row["locked_until"] is None


def test_dead_lettered_event_is_not_reclaimed() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(database_url)
    store = PostgresOutboxStore(engine)
    event_id = _insert_event(database_url)

    event = next(
        item
        for item in store.claim_batch(worker_id="worker-a", limit=10, lease_seconds=30)
        if str(item.id) == event_id
    )
    store.mark_failed(
        event_id=event.id,
        worker_id="worker-a",
        error="permanent provider failure",
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=1),
        dead_letter=True,
    )

    again = store.claim_batch(worker_id="worker-b", limit=100, lease_seconds=30)
    assert all(str(item.id) != event_id for item in again)
