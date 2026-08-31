from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.analytics.models import ActivationJourney, MeaningfulWeighMetric
from kefe_api.modules.analytics.service import MeaningfulWeighsAggregator


def test_meaningful_weighs_aggregator_counts_committed_sessions_in_window() -> None:
    now = datetime.now(UTC)
    window_start = now - timedelta(days=7)
    window_end = now

    actor_1 = uuid4()
    actor_2 = uuid4()
    case_1 = uuid4()
    case_2 = uuid4()

    # Journey 1: Committed inside window by actor_1 on case_1
    j1 = ActivationJourney(
        session_id=uuid4(),
        actor_id=actor_1,
        case_version_id=case_1,
        started_at=now - timedelta(days=2),
        started_source_event_id=uuid4(),
        committed_at=now - timedelta(days=2),
        committed_source_event_id=uuid4(),
        result_revealed_at=now - timedelta(days=2),
        result_revealed_source_event_id=uuid4(),
    )

    # Journey 2: Committed inside window by actor_1 on case_2
    j2 = ActivationJourney(
        session_id=uuid4(),
        actor_id=actor_1,
        case_version_id=case_2,
        started_at=now - timedelta(days=1),
        started_source_event_id=uuid4(),
        committed_at=now - timedelta(days=1),
        committed_source_event_id=uuid4(),
        result_revealed_at=now - timedelta(days=1),
        result_revealed_source_event_id=uuid4(),
    )

    # Journey 3: Committed inside window by actor_2 on case_1
    j3 = ActivationJourney(
        session_id=uuid4(),
        actor_id=actor_2,
        case_version_id=case_1,
        started_at=now - timedelta(hours=3),
        started_source_event_id=uuid4(),
        committed_at=now - timedelta(hours=3),
        committed_source_event_id=uuid4(),
        result_revealed_at=now - timedelta(hours=3),
        result_revealed_source_event_id=uuid4(),
    )

    # Journey 4: Started but NOT committed (mere browse / abandoned)
    j4 = ActivationJourney(
        session_id=uuid4(),
        actor_id=actor_2,
        case_version_id=case_2,
        started_at=now - timedelta(hours=1),
        started_source_event_id=uuid4(),
        committed_at=None,
        committed_source_event_id=None,
        result_revealed_at=None,
        result_revealed_source_event_id=None,
    )

    # Journey 5: Committed OUTSIDE the 7-day window
    j5 = ActivationJourney(
        session_id=uuid4(),
        actor_id=uuid4(),
        case_version_id=case_1,
        started_at=now - timedelta(days=10),
        started_source_event_id=uuid4(),
        committed_at=now - timedelta(days=10),
        committed_source_event_id=uuid4(),
        result_revealed_at=now - timedelta(days=10),
        result_revealed_source_event_id=uuid4(),
    )

    metric = MeaningfulWeighsAggregator.calculate(
        [j1, j2, j3, j4, j5],
        window_start=window_start,
        window_end=window_end,
    )

    assert isinstance(metric, MeaningfulWeighMetric)
    assert metric.meaningful_weigh_count == 3
    assert metric.weekly_active_weighers == 2
    assert metric.distinct_cases_weighed == 2
