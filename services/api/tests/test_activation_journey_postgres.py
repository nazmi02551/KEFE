from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_analytics import PostgresAnalyticsEventStore
from kefe_api.modules.analytics.models import (
    AnalyticsEvent,
    AnalyticsPrivacyClass,
    AnalyticsRetentionClass,
)
from kefe_api.modules.analytics.service import (
    ActivationJourneyProjectionError,
    ActivationJourneyProjector,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)

BASE_TIME = datetime(2026, 8, 29, 8, 0, tzinfo=UTC)


def _event(
    analytics_name: str,
    *,
    session_id: UUID,
    actor_id: UUID | None,
    case_version_id: UUID,
    occurred_at: datetime,
) -> AnalyticsEvent:
    source_names = {
        "activation.weigh_started": "weigh.started",
        "activation.weigh_committed": "weigh.committed",
        "activation.result_revealed": "result.revealed",
    }
    return AnalyticsEvent(
        id=uuid4(),
        source_event_id=uuid4(),
        source_event_name=source_names[analytics_name],
        source_event_version=1,
        analytics_name=analytics_name,
        analytics_version=1,
        occurred_at=occurred_at,
        producer_version="activation-journey-postgres-test",
        actor_id=actor_id,
        session_id=session_id,
        case_version_id=case_version_id,
        contribution_class=(
            "CORE_PRE_RESULT"
            if analytics_name == "activation.weigh_committed"
            else None
        ),
        privacy_class=AnalyticsPrivacyClass.PRODUCT_ANALYTICS,
        retention_class=AnalyticsRetentionClass.STANDARD_13_MONTHS,
        metric_families=("ACTIVATION",),
        payload={},
    )


def test_postgres_activation_journey_is_atomic_and_reproducible() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"], future=True)
    store = PostgresAnalyticsEventStore(engine)
    session_id = uuid4()
    actor_id = uuid4()
    case_version_id = uuid4()
    events = [
        _event(
            "activation.weigh_started",
            session_id=session_id,
            actor_id=actor_id,
            case_version_id=case_version_id,
            occurred_at=BASE_TIME,
        ),
        _event(
            "activation.weigh_committed",
            session_id=session_id,
            actor_id=actor_id,
            case_version_id=case_version_id,
            occurred_at=BASE_TIME + timedelta(minutes=2),
        ),
        _event(
            "activation.result_revealed",
            session_id=session_id,
            actor_id=None,
            case_version_id=case_version_id,
            occurred_at=BASE_TIME + timedelta(minutes=3),
        ),
    ]
    conflicting = _event(
        "activation.weigh_committed",
        session_id=session_id,
        actor_id=uuid4(),
        case_version_id=case_version_id,
        occurred_at=BASE_TIME + timedelta(minutes=1),
    )

    try:
        for event in reversed(events):
            assert store.append_once(event) is True
        assert store.append_once(events[0]) is False

        stored_events = store.list_by_session(session_id)
        stored = store.get_activation_journey(session_id)
        rebuilt = ActivationJourneyProjector().rebuild(stored_events)
        assert stored == rebuilt
        assert stored is not None
        assert stored.actor_id == actor_id
        assert stored.case_version_id == case_version_id
        assert stored.started_source_event_id == events[0].source_event_id
        assert stored.committed_source_event_id == events[1].source_event_id
        assert stored.result_revealed_source_event_id == events[2].source_event_id

        with pytest.raises(ActivationJourneyProjectionError, match="actor_id conflict"):
            store.append_once(conflicting)
        assert store.get(conflicting.id) is None
        assert store.get_activation_journey(session_id) == stored
    finally:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM analytics.activation_journey "
                    "WHERE session_id = :session_id"
                ),
                {"session_id": session_id},
            )
            connection.execute(
                text(
                    "DELETE FROM analytics.analytics_event "
                    "WHERE session_id = :session_id"
                ),
                {"session_id": session_id},
            )
        engine.dispose()
