from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class EquilibriumState(StrEnum):
    OPTIMAL_BALANCE = "OPTIMAL_BALANCE"
    HIGH_DEFICIT_RISK = "HIGH_DEFICIT_RISK"
    SEVERE_SOCIAL_IMPACT = "SEVERE_SOCIAL_IMPACT"
    ENVIRONMENTAL_DEGRADATION = "ENVIRONMENTAL_DEGRADATION"


@dataclass(frozen=True, slots=True)
class PolicySimulationResult:
    simulation_id: str
    case_version_id: UUID
    policy_knob_name: str
    knob_value: float
    fiscal_score: float
    social_score: float
    environmental_score: float
    equilibrium_state: EquilibriumState


class PolicySimulatorCalculator:
    @staticmethod
    def simulate(
        *,
        simulation_id: str,
        case_version_id: UUID,
        policy_knob_name: str,
        knob_value: float,
        fiscal_score: float,
        social_score: float,
        environmental_score: float,
    ) -> PolicySimulationResult:
        if not 0.0 <= knob_value <= 100.0:
            raise ValueError(f"knob_value must be in [0.0, 100.0], got {knob_value}")
        if not 0.0 <= fiscal_score <= 1.0:
            raise ValueError(f"fiscal_score must be in [0.0, 1.0], got {fiscal_score}")
        if not 0.0 <= social_score <= 1.0:
            raise ValueError(f"social_score must be in [0.0, 1.0], got {social_score}")
        if not 0.0 <= environmental_score <= 1.0:
            raise ValueError(f"environmental_score must be in [0.0, 1.0], got {environmental_score}")
        if len(policy_knob_name.strip()) < 3:
            raise ValueError("policy_knob_name must have at least 3 characters")

        if fiscal_score < 0.35:
            state = EquilibriumState.HIGH_DEFICIT_RISK
        elif social_score < 0.35:
            state = EquilibriumState.SEVERE_SOCIAL_IMPACT
        elif environmental_score < 0.35:
            state = EquilibriumState.ENVIRONMENTAL_DEGRADATION
        else:
            state = EquilibriumState.OPTIMAL_BALANCE

        return PolicySimulationResult(
            simulation_id=simulation_id.strip(),
            case_version_id=case_version_id,
            policy_knob_name=policy_knob_name.strip(),
            knob_value=round(knob_value, 1),
            fiscal_score=round(fiscal_score, 2),
            social_score=round(social_score, 2),
            environmental_score=round(environmental_score, 2),
            equilibrium_state=state,
        )
