from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_analytics import PostgresAnalyticsEventStore
from kefe_api.modules.analytics.models import (
    AnalyticsEvent,
    AnalyticsPrivacyClass,
    AnalyticsRetentionClass,
)
from kefe_api.modules.analytics.service import (
    QualityJourneyProjectionError,
    QualityJourneyProjector,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)

BASE_TIME = datetime(2026, 8, 29, 10, 0, tzinfo=UTC)


def _event(
    analytics_name: str,
    *,
    session_id: UUID,
    case_version_id: UUID | None,
    occurred_at: datetime,
) -> AnalyticsEvent:
    source_names = {
        "activation.weigh_committed": "weigh.committed",
        "quality.perspective_viewed": "perspective.viewed",
        "quality.exposure_recorded": "exposure.recorded",
        "quality.intervention_exposed": "intervention.exposed",
        "quality.decision_revised": "decision.revised",
    }
    return AnalyticsEvent(
        id=uuid4(),
        source_event_id=uuid4(),
        source_event_name=source_names[analytics_name],
        source_event_version=1,
        analytics_name=analytics_name,
        analytics_version=1,
        occurred_at=occurred_at,
        producer_version="quality-journey-postgres-test",
        actor_id=None,
        session_id=session_id,
        case_version_id=case_version_id,
        contribution_class=(
            "CORE_PRE_RESULT" if analytics_name == "activation.weigh_committed" else None
        ),
        privacy_class=AnalyticsPrivacyClass.PRODUCT_ANALYTICS,
        retention_class=AnalyticsRetentionClass.STANDARD_13_MONTHS,
        metric_families=("QUALITY",),
        payload={},
    )


def _cleanup(engine, session_id: UUID) -> None:
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM analytics.quality_journey WHERE session_id = :session_id"),
            {"session_id": session_id},
        )
        connection.execute(
            text("DELETE FROM analytics.activation_journey WHERE session_id = :session_id"),
            {"session_id": session_id},
        )
        connection.execute(
            text("DELETE FROM analytics.analytics_event WHERE session_id = :session_id"),
            {"session_id": session_id},
        )


def test_postgres_quality_journey_is_atomic_and_reproducible() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"], future=True)
    store = PostgresAnalyticsEventStore(engine)
    session_id = uuid4()
    case_version_id = uuid4()
    names = (
        "activation.weigh_committed",
        "quality.perspective_viewed",
        "quality.exposure_recorded",
        "quality.intervention_exposed",
        "quality.decision_revised",
    )
    events = [
        _event(
            name,
            session_id=session_id,
            case_version_id=(case_version_id if index < 2 else None),
            occurred_at=BASE_TIME + timedelta(minutes=index),
        )
        for index, name in enumerate(names)
    ]
    conflicting = _event(
        "quality.decision_revised",
        session_id=session_id,
        case_version_id=uuid4(),
        occurred_at=BASE_TIME + timedelta(minutes=10),
    )

    try:
        _cleanup(engine, session_id)
        for event in reversed(events):
            assert store.append_once(event) is True
        assert store.append_once(events[0]) is False

        stored_events = store.list_by_session(session_id)
        stored = store.get_quality_journey(session_id)
        rebuilt = QualityJourneyProjector().rebuild(stored_events)
        assert stored == rebuilt
        assert stored is not None
        assert stored.case_version_id == case_version_id
        assert stored.committed_source_event_id == events[0].source_event_id
        assert stored.perspective_viewed_source_event_id == events[1].source_event_id
        assert stored.exposure_recorded_source_event_id == events[2].source_event_id
        assert stored.intervention_exposed_source_event_id == events[3].source_event_id
        assert stored.decision_revised_source_event_id == events[4].source_event_id

        with pytest.raises(
            QualityJourneyProjectionError,
            match="case_version_id conflict",
        ):
            store.append_once(conflicting)
        assert store.get(conflicting.id) is None
        assert store.get_quality_journey(session_id) == stored
    finally:
        _cleanup(engine, session_id)
        engine.dispose()


def test_postgres_dual_projection_rolls_back_activation_on_quality_conflict() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"], future=True)
    store = PostgresAnalyticsEventStore(engine)
    session_id = uuid4()
    case_version_id = uuid4()
    perspective = _event(
        "quality.perspective_viewed",
        session_id=session_id,
        case_version_id=case_version_id,
        occurred_at=BASE_TIME,
    )
    commit = _event(
        "activation.weigh_committed",
        session_id=session_id,
        case_version_id=uuid4(),
        occurred_at=BASE_TIME + timedelta(minutes=1),
    )

    try:
        _cleanup(engine, session_id)
        assert store.append_once(perspective) is True
        with pytest.raises(
            QualityJourneyProjectionError,
            match="case_version_id conflict",
        ):
            store.append_once(commit)

        assert store.get(commit.id) is None
        assert store.get_activation_journey(session_id) is None
        assert store.list_by_session(session_id) == (perspective,)
    finally:
        _cleanup(engine, session_id)
        engine.dispose()


def test_postgres_0041_backfills_existing_quality_events() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    engine = create_engine(database_url, future=True)
    session_id = uuid4()
    case_version_id = uuid4()
    perspective_source_id = uuid4()
    revision_source_id = uuid4()
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

    command.downgrade(config, "20260829_0040")
    try:
        with engine.begin() as connection:
            for event_id, source_event_id, source_name, name, occurred_at, case_id in (
                (
                    uuid4(),
                    perspective_source_id,
                    "perspective.viewed",
                    "quality.perspective_viewed",
                    BASE_TIME,
                    case_version_id,
                ),
                (
                    uuid4(),
                    revision_source_id,
                    "decision.revised",
                    "quality.decision_revised",
                    BASE_TIME + timedelta(minutes=1),
                    None,
                ),
            ):
                connection.execute(
                    text(
                        """
                        INSERT INTO analytics.analytics_event (
                            id, source_event_id, source_event_name,
                            source_event_version, analytics_name,
                            analytics_version, occurred_at, producer_version,
                            actor_id, session_id, case_version_id,
                            contribution_class, privacy_class, retention_class,
                            metric_families, payload
                        ) VALUES (
                            :id, :source_event_id, :source_event_name,
                            1, :analytics_name, 1, :occurred_at,
                            '0041-backfill-test', NULL, :session_id,
                            :case_version_id, NULL, 'PRODUCT_ANALYTICS',
                            'STANDARD_13_MONTHS', '["QUALITY"]'::jsonb,
                            '{}'::jsonb
                        )
                        """
                    ),
                    {
                        "id": event_id,
                        "source_event_id": source_event_id,
                        "source_event_name": source_name,
                        "analytics_name": name,
                        "occurred_at": occurred_at,
                        "session_id": session_id,
                        "case_version_id": case_id,
                    },
                )

        command.upgrade(config, "head")

        with engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        case_version_id,
                        perspective_viewed_source_event_id,
                        decision_revised_source_event_id
                    FROM analytics.quality_journey
                    WHERE session_id = :session_id
                    """
                ),
                {"session_id": session_id},
            ).one()
        assert tuple(row) == (
            case_version_id,
            perspective_source_id,
            revision_source_id,
        )
    finally:
        command.upgrade(config, "head")
        _cleanup(engine, session_id)
        engine.dispose()
