from __future__ import annotations

from kefe_api.modules.decision.fatigue_guard import (
    DecisionFatigueCalculator,
    DecisionFatigueResult,
    PacingStatus,
)


def test_fatigue_guard_evaluates_pacing() -> None:
    r = DecisionFatigueCalculator.evaluate(
        session_id="sess_abc123",
        consecutive_weigh_count=6,
        session_duration_minutes=25.0,
    )

    assert isinstance(r, DecisionFatigueResult)
    assert r.pacing_status == PacingStatus.PACING_RECOMMENDED
    assert r.consecutive_weigh_count == 6


def test_fatigue_guard_rest_interval() -> None:
    r = DecisionFatigueCalculator.evaluate(
        session_id="sess_abc123",
        consecutive_weigh_count=12,
        session_duration_minutes=50.0,
    )

    assert r.pacing_status == PacingStatus.REST_INTERVAL_ACTIVE


def test_fatigue_guard_invalid_count() -> None:
    failed = False
    try:
        DecisionFatigueCalculator.evaluate(
            session_id="sess_abc",
            consecutive_weigh_count=-1,
            session_duration_minutes=10.0,
        )
    except ValueError:
        failed = True

    assert failed is True
