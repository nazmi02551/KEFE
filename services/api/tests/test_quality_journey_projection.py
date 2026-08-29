from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from kefe_api.modules.analytics.in_memory import InMemoryAnalyticsEventStore
from kefe_api.modules.analytics.models import (
    AnalyticsEvent,
    AnalyticsPrivacyClass,
    AnalyticsRetentionClass,
    QualityJourney,
)
from kefe_api.modules.analytics.service import (
    QualityJourneyProjectionError,
    QualityJourneyProjector,
)

BASE_TIME = datetime(2026, 8, 29, 10, 0, tzinfo=UTC)


def _event(
    analytics_name: str,
    *,
    session_id: UUID,
    case_version_id: UUID | None,
    occurred_at: datetime,
    source_event_id: UUID | None = None,
) -> AnalyticsEvent:
    source_names = {
        "activation.weigh_committed": "weigh.committed",
        "quality.perspective_viewed": "perspective.viewed",
        "quality.exposure_recorded": "exposure.recorded",
        "quality.intervention_exposed": "intervention.exposed",
        "quality.decision_revised": "decision.revised",
        "activation.weigh_started": "weigh.started",
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
        producer_version="quality-journey-test",
        actor_id=None,
        session_id=session_id,
        case_version_id=case_version_id,
        contribution_class=(
            "CORE_PRE_RESULT" if analytics_name == "activation.weigh_committed" else None
        ),
        privacy_class=AnalyticsPrivacyClass.PRODUCT_ANALYTICS,
        retention_class=AnalyticsRetentionClass.STANDARD_13_MONTHS,
        metric_families=("QUALITY",),
        payload={"must_not_copy": True},
    )


def _journey_events() -> tuple[list[AnalyticsEvent], UUID, UUID]:
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
            case_version_id=(
                case_version_id
                if name in {"activation.weigh_committed", "quality.perspective_viewed"}
                else None
            ),
            occurred_at=BASE_TIME + timedelta(minutes=index),
        )
        for index, name in enumerate(names)
    ]
    return events, session_id, case_version_id


def test_rebuild_is_order_independent_and_keeps_source_lineage() -> None:
    events, session_id, case_version_id = _journey_events()
    projector = QualityJourneyProjector()

    forward = projector.rebuild(events)
    reverse = projector.rebuild(reversed(events))

    assert forward == reverse
    assert forward == QualityJourney(
        session_id=session_id,
        case_version_id=case_version_id,
        committed_at=events[0].occurred_at,
        committed_source_event_id=events[0].source_event_id,
        perspective_viewed_at=events[1].occurred_at,
        perspective_viewed_source_event_id=events[1].source_event_id,
        exposure_recorded_at=events[2].occurred_at,
        exposure_recorded_source_event_id=events[2].source_event_id,
        intervention_exposed_at=events[3].occurred_at,
        intervention_exposed_source_event_id=events[3].source_event_id,
        decision_revised_at=events[4].occurred_at,
        decision_revised_source_event_id=events[4].source_event_id,
    )
    assert not hasattr(forward, "actor_id")
    assert not hasattr(forward, "payload")


def test_same_stage_selects_deterministic_earliest_observation() -> None:
    _, session_id, case_version_id = _journey_events()
    higher_id = UUID("00000000-0000-0000-0000-000000000002")
    lower_id = UUID("00000000-0000-0000-0000-000000000001")
    events = [
        _event(
            "quality.perspective_viewed",
            session_id=session_id,
            case_version_id=case_version_id,
            occurred_at=BASE_TIME,
            source_event_id=higher_id,
        ),
        _event(
            "quality.perspective_viewed",
            session_id=session_id,
            case_version_id=case_version_id,
            occurred_at=BASE_TIME,
            source_event_id=lower_id,
        ),
    ]

    journey = QualityJourneyProjector().rebuild(events)

    assert journey is not None
    assert journey.perspective_viewed_source_event_id == lower_id


def test_optional_case_version_is_filled_by_later_observation() -> None:
    events, session_id, case_version_id = _journey_events()
    projector = QualityJourneyProjector()

    current = projector.apply(None, events[2])
    completed = projector.apply(current, events[1])

    assert current is not None and current.case_version_id is None
    assert completed is not None and completed.case_version_id == case_version_id


def test_memory_store_rejects_case_conflict_atomically() -> None:
    events, session_id, case_version_id = _journey_events()
    store = InMemoryAnalyticsEventStore()
    assert store.append_once(events[1]) is True
    before = store.get_quality_journey(session_id)
    conflicting = _event(
        "quality.decision_revised",
        session_id=session_id,
        case_version_id=uuid4(),
        occurred_at=BASE_TIME + timedelta(minutes=10),
    )

    with pytest.raises(QualityJourneyProjectionError, match="case_version_id conflict"):
        store.append_once(conflicting)

    assert before is not None and before.case_version_id == case_version_id
    assert store.get(conflicting.id) is None
    assert store.get_quality_journey(session_id) == before
    assert store.list_by_session(session_id) == (events[1],)


def test_memory_dual_projection_rolls_back_activation_on_quality_conflict() -> None:
    _, session_id, case_version_id = _journey_events()
    store = InMemoryAnalyticsEventStore()
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
    assert store.append_once(perspective) is True

    with pytest.raises(QualityJourneyProjectionError, match="case_version_id conflict"):
        store.append_once(commit)

    assert store.get(commit.id) is None
    assert store.get_activation_journey(session_id) is None
    assert store.list_by_session(session_id) == (perspective,)


def test_non_quality_event_does_not_create_quality_journey() -> None:
    _, session_id, case_version_id = _journey_events()
    event = _event(
        "activation.weigh_started",
        session_id=session_id,
        case_version_id=case_version_id,
        occurred_at=BASE_TIME,
    )
    store = InMemoryAnalyticsEventStore()

    assert store.append_once(event) is True
    assert store.get_quality_journey(session_id) is None
