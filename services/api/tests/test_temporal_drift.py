from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.decision.temporal_drift import (
    DriftNature,
    TemporalDriftCalculator,
    TemporalDriftResult,
)


def test_temporal_drift_calculator_evaluates_shifts_accurately() -> None:
    case_id = uuid4()
    t0 = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    t_later = t0 + timedelta(days=45)

    # 1. Matured Revision (shifted after 45 days)
    r1 = TemporalDriftCalculator.calculate_drift(
        case_version_id=case_id,
        initial_option_code="OPT_A",
        retest_option_code="OPT_B",
        initial_timestamp=t0,
        retest_timestamp=t_later,
        initial_confidence=0.6,
        retest_confidence=0.8,
    )
    assert isinstance(r1, TemporalDriftResult)
    assert r1.is_shifted is True
    assert r1.time_elapsed_days == 45
    assert r1.drift_nature == DriftNature.MATURED_REVISION

    # 2. Stable Conviction (same choice after 45 days)
    r2 = TemporalDriftCalculator.calculate_drift(
        case_version_id=case_id,
        initial_option_code="OPT_A",
        retest_option_code="OPT_A",
        initial_timestamp=t0,
        retest_timestamp=t_later,
        initial_confidence=0.6,
        retest_confidence=0.6,
    )
    assert r2.is_shifted is False
    assert r2.drift_nature == DriftNature.STABLE_CONVICTION

    # 3. Reinforced Certainty (same choice, confidence jumped from 0.4 to 0.9)
    r3 = TemporalDriftCalculator.calculate_drift(
        case_version_id=case_id,
        initial_option_code="OPT_A",
        retest_option_code="OPT_A",
        initial_timestamp=t0,
        retest_timestamp=t_later,
        initial_confidence=0.4,
        retest_confidence=0.9,
    )
    assert r3.drift_nature == DriftNature.REINFORCED_CERTAINTY
