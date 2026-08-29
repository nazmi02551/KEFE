from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from kefe_api.modules.analytics.in_memory import InMemoryAnalyticsEventStore
from kefe_api.modules.analytics.models import (
    ActivationJourney,
    AnalyticsEvent,
    AnalyticsPrivacyClass,
    AnalyticsRetentionClass,
)
from kefe_api.modules.analytics.service import (
    ActivationJourneyProjectionError,
    ActivationJourneyProjector,
)

BASE_TIME = datetime(2026, 8, 29, 8, 0, tzinfo=UTC)


def _event(
    analytics_name: str,
    *,
    session_id: UUID,
    actor_id: UUID | None,
    case_version_id: UUID,
    occurred_at: datetime,
    source_event_id: UUID | None = None,
) -> AnalyticsEvent:
    source_names = {
        "activation.weigh_started": "weigh.started",
        "activation.weigh_committed": "weigh.committed",
        "activation.result_revealed": "result.revealed",
        "quality.perspective_viewed": "perspective.viewed",
    }
    source_id = source_event_id or uuid4()
    return AnalyticsEvent(
        id=uuid4(),
        source_event_id=source_id,
        source_event_name=source_names[analytics_name],
        source_event_version=1,
        analytics_name=analytics_name,
        analytics_version=1,
        occurred_at=occurred_at,
        producer_version="activation-journey-test",
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
        metric_families=(
            ("QUALITY",)
            if analytics_name == "quality.perspective_viewed"
            else ("ACTIVATION",)
        ),
        payload={},
    )


def _journey_events() -> tuple[list[AnalyticsEvent], UUID, UUID, UUID]:
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
    return events, session_id, actor_id, case_version_id


def test_rebuild_is_order_independent_and_keeps_source_lineage() -> None:
    events, session_id, actor_id, case_version_id = _journey_events()
    projector = ActivationJourneyProjector()

    forward = projector.rebuild(events)
    reverse = projector.rebuild(reversed(events))

    assert forward == reverse
    assert forward == ActivationJourney(
        session_id=session_id,
        actor_id=actor_id,
        case_version_id=case_version_id,
        started_at=events[0].occurred_at,
        started_source_event_id=events[0].source_event_id,
        committed_at=events[1].occurred_at,
        committed_source_event_id=events[1].source_event_id,
        result_revealed_at=events[2].occurred_at,
        result_revealed_source_event_id=events[2].source_event_id,
    )


def test_repeated_stage_selects_deterministic_earliest_observation() -> None:
    events, session_id, actor_id, case_version_id = _journey_events()
    later_start = _event(
        "activation.weigh_started",
        session_id=session_id,
        actor_id=actor_id,
        case_version_id=case_version_id,
        occurred_at=BASE_TIME + timedelta(seconds=1),
    )

    journey = ActivationJourneyProjector().rebuild([later_start, *events])

    assert journey is not None
    assert journey.started_at == events[0].occurred_at
    assert journey.started_source_event_id == events[0].source_event_id


def test_same_timestamp_stage_uses_source_event_id_tie_breaker() -> None:
    _, session_id, actor_id, case_version_id = _journey_events()
    higher_id = UUID("00000000-0000-0000-0000-000000000002")
    lower_id = UUID("00000000-0000-0000-0000-000000000001")
    events = [
        _event(
            "activation.weigh_started",
            session_id=session_id,
            actor_id=actor_id,
            case_version_id=case_version_id,
            occurred_at=BASE_TIME,
            source_event_id=higher_id,
        ),
        _event(
            "activation.weigh_started",
            session_id=session_id,
            actor_id=actor_id,
            case_version_id=case_version_id,
            occurred_at=BASE_TIME,
            source_event_id=lower_id,
        ),
    ]

    journey = ActivationJourneyProjector().rebuild(events)

    assert journey is not None
    assert journey.started_source_event_id == lower_id


def test_memory_store_out_of_order_matches_rebuild() -> None:
    events, session_id, _, _ = _journey_events()
    store = InMemoryAnalyticsEventStore()
    for event in reversed(events):
        assert store.append_once(event) is True

    assert store.get_activation_journey(session_id) == (
        ActivationJourneyProjector().rebuild(events)
    )


def test_memory_store_updates_event_and_journey_atomically() -> None:
    events, session_id, actor_id, case_version_id = _journey_events()
    store = InMemoryAnalyticsEventStore()
    assert store.append_once(events[0]) is True
    before = store.get_activation_journey(session_id)

    conflicting = _event(
        "activation.weigh_committed",
        session_id=session_id,
        actor_id=uuid4(),
        case_version_id=case_version_id,
        occurred_at=BASE_TIME + timedelta(minutes=1),
    )
    with pytest.raises(ActivationJourneyProjectionError, match="actor_id conflict"):
        store.append_once(conflicting)

    assert store.get(conflicting.id) is None
    assert store.get_activation_journey(session_id) == before
    assert store.list_by_session(session_id) == (events[0],)
    assert before is not None and before.actor_id == actor_id


def test_case_version_conflict_fails_closed() -> None:
    events, session_id, actor_id, _ = _journey_events()
    projector = ActivationJourneyProjector()
    current = projector.apply(None, events[0])
    conflicting = _event(
        "activation.result_revealed",
        session_id=session_id,
        actor_id=actor_id,
        case_version_id=uuid4(),
        occurred_at=BASE_TIME + timedelta(minutes=1),
    )

    with pytest.raises(ActivationJourneyProjectionError, match="case_version_id conflict"):
        projector.apply(current, conflicting)


def test_non_activation_event_is_stored_without_creating_journey() -> None:
    _, session_id, actor_id, case_version_id = _journey_events()
    event = _event(
        "quality.perspective_viewed",
        session_id=session_id,
        actor_id=actor_id,
        case_version_id=case_version_id,
        occurred_at=BASE_TIME,
    )
    store = InMemoryAnalyticsEventStore()

    assert store.append_once(event) is True
    assert store.get(event.id) == event
    assert store.get_activation_journey(session_id) is None
