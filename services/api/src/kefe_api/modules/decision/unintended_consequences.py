from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ConsequenceType(StrEnum):
    PERVERSE_INCENTIVE = "PERVERSE_INCENTIVE"
    MARKET_DISTORTION = "MARKET_DISTORTION"
    BEHAVIORAL_REBOUND = "BEHAVIORAL_REBOUND"
    SYSTEMIC_DISPLACEMENT = "SYSTEMIC_DISPLACEMENT"


class ConsequenceSeverity(StrEnum):
    LOW_DRIFT = "LOW_DRIFT"
    MODERATE_IMPACT = "MODERATE_IMPACT"
    SEVERE_PARADOX = "SEVERE_PARADOX"


@dataclass(frozen=True, slots=True)
class UnintendedConsequenceItem:
    consequence_type: ConsequenceType
    severity: ConsequenceSeverity
    mitigation_feasibility: float
    description: str


@dataclass(frozen=True, slots=True)
class UnintendedConsequencesResult:
    case_version_id: UUID
    option_code: str
    overall_systemic_risk: ConsequenceSeverity
    consequences: tuple[UnintendedConsequenceItem, ...]


class UnintendedConsequencesCalculator:
    @staticmethod
    def simulate(
        *,
        case_version_id: UUID,
        option_code: str,
        consequences: list[UnintendedConsequenceItem],
    ) -> UnintendedConsequencesResult:
        if not consequences:
            raise ValueError("consequences must not be empty")

        for c in consequences:
            if not 0.0 <= c.mitigation_feasibility <= 1.0:
                raise ValueError(f"mitigation_feasibility must be in [0.0, 1.0], got {c.mitigation_feasibility}")

        has_severe = any(c.severity == ConsequenceSeverity.SEVERE_PARADOX for c in consequences)
        has_moderate = any(c.severity == ConsequenceSeverity.MODERATE_IMPACT for c in consequences)

        if has_severe:
            overall = ConsequenceSeverity.SEVERE_PARADOX
        elif has_moderate:
            overall = ConsequenceSeverity.MODERATE_IMPACT
        else:
            overall = ConsequenceSeverity.LOW_DRIFT

        return UnintendedConsequencesResult(
            case_version_id=case_version_id,
            option_code=option_code.strip(),
            overall_systemic_risk=overall,
            consequences=tuple(consequences),
        )
