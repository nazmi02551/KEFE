from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_analytics import PostgresAnalyticsEventStore
from kefe_api.modules.analytics.registry import default_analytics_registry
from kefe_api.modules.analytics.service import AnalyticsEventProjector
from kefe_api.modules.events.models import OutboxEvent

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def test_postgres_analytics_store_is_idempotent() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"], future=True)
    source_event_id = uuid4()
    actor_id = uuid4()
    case_version_id = uuid4()
    session_id = uuid4()
    source = OutboxEvent(
        id=source_event_id,
        aggregate_type="weigh_session",
        aggregate_id=session_id,
        event_name="weigh.committed",
        event_version=1,
        occurred_at=datetime(2026, 8, 1, 12, 0, tzinfo=UTC),
        payload={
            "actor_id": str(actor_id),
            "case_version_id": str(case_version_id),
            "committed_at": "2026-08-01T12:00:00+00:00",
            "has_reason": True,
            "internal_debug": "must not persist",
        },
        attempts=1,
    )
    projected = AnalyticsEventProjector(
        registry=default_analytics_registry(),
        producer_version="postgres-test",
    ).project(source)
    assert projected is not None

    store = PostgresAnalyticsEventStore(engine)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM analytics.analytics_event "
                    "WHERE source_event_id = :source_event_id"
                ),
                {"source_event_id": source_event_id},
            )

        assert store.append_once(projected) is True
        assert store.append_once(projected) is False

        stored = store.get(projected.id)
        assert stored is not None
        assert stored.actor_id == actor_id
        assert stored.session_id == session_id
        assert stored.case_version_id == case_version_id
        assert stored.contribution_class == "CORE_PRE_RESULT"
        assert stored.payload == {
            "committed_at": "2026-08-01T12:00:00+00:00",
            "has_reason": True,
        }
        assert store.list_by_source_event(source_event_id) == (stored,)
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM analytics.analytics_event "
                    "WHERE source_event_id = :source_event_id"
                ),
                {"source_event_id": source_event_id},
            )
        engine.dispose()
