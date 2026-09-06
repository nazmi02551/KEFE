from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.signal_half_life import (
    FreshnessState,
    SignalHalfLifeCalculator,
    SignalHalfLifeResult,
)


def test_signal_half_life_calculator_evaluates_decay() -> None:
    case_id = uuid4()

    r = SignalHalfLifeCalculator.evaluate(
        signal_id="sig_94812",
        case_version_id=case_id,
        half_life_days=90,
        age_days=90.0,
    )

    assert isinstance(r, SignalHalfLifeResult)
    assert r.remaining_weight == 0.50
    assert r.freshness_state == FreshnessState.STABLE


def test_signal_half_life_expired() -> None:
    case_id = uuid4()

    r = SignalHalfLifeCalculator.evaluate(
        signal_id="sig_old",
        case_version_id=case_id,
        half_life_days=30,
        age_days=120.0,
    )

    assert r.freshness_state == FreshnessState.EXPIRED_NEEDS_RETEST


def test_signal_half_life_invalid_input() -> None:
    case_id = uuid4()
    failed = False
    try:
        SignalHalfLifeCalculator.evaluate(
            signal_id="s",
            case_version_id=case_id,
            half_life_days=-10,
            age_days=5.0,
        )
    except ValueError:
        failed = True

    assert failed is True
