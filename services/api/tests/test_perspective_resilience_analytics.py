from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.analytics.models import (
    PerspectiveResilienceMetric,
    QualityJourney,
)
from kefe_api.modules.analytics.service import PerspectiveResilienceCalculator


def test_perspective_resilience_calculator_computes_stability_and_shift() -> None:
    now = datetime.now(UTC)
    window_start = now - timedelta(days=7)
    window_end = now

    case_id = uuid4()
    s1, s2, s3, s4 = uuid4(), uuid4(), uuid4(), uuid4()

    # Session 1: Exposed to perspective and REVISED (attitude shifted)
    q1 = QualityJourney(
        session_id=s1,
        case_version_id=case_id,
        committed_at=now - timedelta(days=3),
        committed_source_event_id=uuid4(),
        perspective_viewed_at=now - timedelta(days=3),
        perspective_viewed_source_event_id=uuid4(),
        exposure_recorded_at=now - timedelta(days=3),
        exposure_recorded_source_event_id=uuid4(),
        intervention_exposed_at=None,
        intervention_exposed_source_event_id=None,
        decision_revised_at=now - timedelta(days=3),
        decision_revised_source_event_id=uuid4(),
    )

    # Session 2: Exposed to perspective but did NOT revise (stable decision)
    q2 = QualityJourney(
        session_id=s2,
        case_version_id=case_id,
        committed_at=now - timedelta(days=2),
        committed_source_event_id=uuid4(),
        perspective_viewed_at=now - timedelta(days=2),
        perspective_viewed_source_event_id=uuid4(),
        exposure_recorded_at=now - timedelta(days=2),
        exposure_recorded_source_event_id=uuid4(),
        intervention_exposed_at=None,
        intervention_exposed_source_event_id=None,
        decision_revised_at=None,
        decision_revised_source_event_id=None,
    )

    # Session 3: Exposed to perspective but did NOT revise (stable decision)
    q3 = QualityJourney(
        session_id=s3,
        case_version_id=case_id,
        committed_at=now - timedelta(days=1),
        committed_source_event_id=uuid4(),
        perspective_viewed_at=now - timedelta(days=1),
        perspective_viewed_source_event_id=uuid4(),
        exposure_recorded_at=now - timedelta(days=1),
        exposure_recorded_source_event_id=uuid4(),
        intervention_exposed_at=None,
        intervention_exposed_source_event_id=None,
        decision_revised_at=None,
        decision_revised_source_event_id=None,
    )

    # Session 4: Not exposed to perspective in window (committed only)
    q4 = QualityJourney(
        session_id=s4,
        case_version_id=case_id,
        committed_at=now - timedelta(hours=4),
        committed_source_event_id=uuid4(),
        perspective_viewed_at=None,
        perspective_viewed_source_event_id=None,
        exposure_recorded_at=None,
        exposure_recorded_source_event_id=None,
        intervention_exposed_at=None,
        intervention_exposed_source_event_id=None,
        decision_revised_at=None,
        decision_revised_source_event_id=None,
    )

    metric = PerspectiveResilienceCalculator.calculate(
        [q1, q2, q3, q4],
        window_start=window_start,
        window_end=window_end,
    )

    assert isinstance(metric, PerspectiveResilienceMetric)
    assert metric.total_exposed_sessions == 3
    assert metric.stable_decisions_count == 2
    assert metric.shifted_decisions_count == 1
    assert metric.resilience_index == round(2 / 3, 4)
    assert metric.attitude_shift_rate == round(1 / 3, 4)
