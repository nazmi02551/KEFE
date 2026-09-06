from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.depolarization_index import (
    BridgeEfficacyState,
    DepolarizationCalculator,
    DepolarizationIndexResult,
)


def test_depolarization_calculator_evaluates_high_depolarization() -> None:
    case_id = uuid4()

    r = DepolarizationCalculator.calculate(
        case_version_id=case_id,
        pre_deliberation_distance=0.80,
        post_deliberation_distance=0.30,  # delta = 0.50 / 0.80 = 0.625 >= 0.50
    )

    assert isinstance(r, DepolarizationIndexResult)
    assert r.bridge_efficacy_state == BridgeEfficacyState.HIGH_DEPOLARIZATION
    assert r.depolarization_score == 0.62


def test_depolarization_calculator_persistent_polarization() -> None:
    case_id = uuid4()

    r = DepolarizationCalculator.calculate(
        case_version_id=case_id,
        pre_deliberation_distance=0.85,
        post_deliberation_distance=0.80,  # delta = 0.05 / 0.85 = 0.06 < 0.20
    )

    assert r.bridge_efficacy_state == BridgeEfficacyState.PERSISTENT_POLARIZATION


def test_depolarization_invalid_distance() -> None:
    case_id = uuid4()
    failed = False
    try:
        DepolarizationCalculator.calculate(
            case_version_id=case_id,
            pre_deliberation_distance=1.50,  # > 1.0
            post_deliberation_distance=0.50,
        )
    except ValueError:
        failed = True

    assert failed is True
