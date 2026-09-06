from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.policy_simulator import (
    EquilibriumState,
    PolicySimulationResult,
    PolicySimulatorCalculator,
)


def test_policy_simulator_evaluates_optimal_balance() -> None:
    case_id = uuid4()

    r = PolicySimulatorCalculator.simulate(
        simulation_id="sim_001",
        case_version_id=case_id,
        policy_knob_name="Karbon Vergisi Oranı",
        knob_value=25.0,
        fiscal_score=0.75,
        social_score=0.68,
        environmental_score=0.82,
    )

    assert isinstance(r, PolicySimulationResult)
    assert r.equilibrium_state == EquilibriumState.OPTIMAL_BALANCE
    assert r.policy_knob_name == "Karbon Vergisi Oranı"


def test_policy_simulator_detects_high_deficit() -> None:
    case_id = uuid4()

    r = PolicySimulatorCalculator.simulate(
        simulation_id="sim_002",
        case_version_id=case_id,
        policy_knob_name="Süper Sübvansiyon",
        knob_value=80.0,
        fiscal_score=0.20,
        social_score=0.90,
        environmental_score=0.70,
    )

    assert r.equilibrium_state == EquilibriumState.HIGH_DEFICIT_RISK


def test_policy_simulator_invalid_knob() -> None:
    case_id = uuid4()
    failed = False
    try:
        PolicySimulatorCalculator.simulate(
            simulation_id="sim_003",
            case_version_id=case_id,
            policy_knob_name="K",
            knob_value=150.0,  # > 100
            fiscal_score=0.5,
            social_score=0.5,
            environmental_score=0.5,
        )
    except ValueError:
        failed = True

    assert failed is True
