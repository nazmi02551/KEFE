from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.analytics.models import (
    ActivationFunnelMetric,
    ActivationJourney,
    QualityJourney,
)
from kefe_api.modules.analytics.service import ActivationFunnelCalculator


def test_activation_funnel_calculator_computes_conversion_and_dropoff() -> None:
    now = datetime.now(UTC)
    window_start = now - timedelta(days=7)
    window_end = now

    case_id = uuid4()
    s1, s2, s3, s4 = uuid4(), uuid4(), uuid4(), uuid4()

    # Session 1: Completed full funnel (started, committed, revealed, viewed perspective, revised)
    j1 = ActivationJourney(
        session_id=s1,
        actor_id=uuid4(),
        case_version_id=case_id,
        started_at=now - timedelta(days=2),
        started_source_event_id=uuid4(),
        committed_at=now - timedelta(days=2),
        committed_source_event_id=uuid4(),
        result_revealed_at=now - timedelta(days=2),
        result_revealed_source_event_id=uuid4(),
    )
    q1 = QualityJourney(
        session_id=s1,
        case_version_id=case_id,
        committed_at=now - timedelta(days=2),
        committed_source_event_id=uuid4(),
        perspective_viewed_at=now - timedelta(days=2),
        perspective_viewed_source_event_id=uuid4(),
        exposure_recorded_at=now - timedelta(days=2),
        exposure_recorded_source_event_id=uuid4(),
        intervention_exposed_at=None,
        intervention_exposed_source_event_id=None,
        decision_revised_at=now - timedelta(days=2),
        decision_revised_source_event_id=uuid4(),
    )

    # Session 2: Started, committed, revealed (no perspective, no revision)
    j2 = ActivationJourney(
        session_id=s2,
        actor_id=uuid4(),
        case_version_id=case_id,
        started_at=now - timedelta(days=1),
        started_source_event_id=uuid4(),
        committed_at=now - timedelta(days=1),
        committed_source_event_id=uuid4(),
        result_revealed_at=now - timedelta(days=1),
        result_revealed_source_event_id=uuid4(),
    )

    # Session 3: Started and committed, but not revealed yet
    j3 = ActivationJourney(
        session_id=s3,
        actor_id=uuid4(),
        case_version_id=case_id,
        started_at=now - timedelta(hours=5),
        started_source_event_id=uuid4(),
        committed_at=now - timedelta(hours=5),
        committed_source_event_id=uuid4(),
        result_revealed_at=None,
        result_revealed_source_event_id=None,
    )

    # Session 4: Started but bounced immediately
    j4 = ActivationJourney(
        session_id=s4,
        actor_id=uuid4(),
        case_version_id=case_id,
        started_at=now - timedelta(hours=1),
        started_source_event_id=uuid4(),
        committed_at=None,
        committed_source_event_id=None,
        result_revealed_at=None,
        result_revealed_source_event_id=None,
    )

    metric = ActivationFunnelCalculator.calculate(
        [j1, j2, j3, j4],
        [q1],
        window_start=window_start,
        window_end=window_end,
    )

    assert isinstance(metric, ActivationFunnelMetric)
    assert metric.total_sessions == 4

    stages = {s.stage_name: s for s in metric.stages}

    # Stage 1: WEIGH_STARTED -> 4
    assert stages["WEIGH_STARTED"].stage_count == 4
    assert stages["WEIGH_STARTED"].conversion_from_start_rate == 1.0

    # Stage 2: DECISION_COMMITTED -> 3
    assert stages["DECISION_COMMITTED"].stage_count == 3
    assert stages["DECISION_COMMITTED"].conversion_from_start_rate == 0.75
    assert stages["DECISION_COMMITTED"].drop_off_from_previous_rate == 0.25

    # Stage 3: RESULT_REVEALED -> 2
    assert stages["RESULT_REVEALED"].stage_count == 2
    assert stages["RESULT_REVEALED"].conversion_from_start_rate == 0.50

    # Stage 4: PERSPECTIVE_VIEWED -> 1
    assert stages["PERSPECTIVE_VIEWED"].stage_count == 1
    assert stages["PERSPECTIVE_VIEWED"].conversion_from_start_rate == 0.25

    # Stage 5: DECISION_REVISED -> 1
    assert stages["DECISION_REVISED"].stage_count == 1
    assert stages["DECISION_REVISED"].conversion_from_start_rate == 0.25
