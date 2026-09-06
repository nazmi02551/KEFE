from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ReversibilityClass(StrEnum):
    FULLY_REVERSIBLE = "FULLY_REVERSIBLE"
    CONDITIONALLY_REVERSIBLE = "CONDITIONALLY_REVERSIBLE"
    SUBSTANTIALLY_IRREVERSIBLE = "SUBSTANTIALLY_IRREVERSIBLE"
    PERMANENTLY_IRREVERSIBLE = "PERMANENTLY_IRREVERSIBLE"


@dataclass(frozen=True, slots=True)
class IrreversibilityRiskResult:
    case_version_id: UUID
    option_code: str
    reversibility_class: ReversibilityClass
    precautionary_risk_score: float
    unwind_time_months: int
    unwind_cost_factor: float
    risk_summary: str


class IrreversibilityRiskCalculator:
    @staticmethod
    def evaluate(
        *,
        case_version_id: UUID,
        option_code: str,
        unwind_time_months: int,
        unwind_cost_factor: float,
        is_permanent_physical_damage: bool = False,
        risk_summary: str,
    ) -> IrreversibilityRiskResult:
        if unwind_time_months < 0:
            raise ValueError("unwind_time_months must be >= 0")
        if not 0.0 <= unwind_cost_factor <= 1.0:
            raise ValueError("unwind_cost_factor must be in [0.0, 1.0]")

        if is_permanent_physical_damage:
            rev_class = ReversibilityClass.PERMANENTLY_IRREVERSIBLE
            risk_score = 1.00
        elif unwind_time_months > 36 or unwind_cost_factor >= 0.75:
            rev_class = ReversibilityClass.SUBSTANTIALLY_IRREVERSIBLE
            risk_score = round(0.70 + (unwind_cost_factor * 0.25), 2)
        elif unwind_time_months > 6 or unwind_cost_factor >= 0.30:
            rev_class = ReversibilityClass.CONDITIONALLY_REVERSIBLE
            risk_score = round(0.35 + (unwind_cost_factor * 0.30), 2)
        else:
            rev_class = ReversibilityClass.FULLY_REVERSIBLE
            risk_score = round(unwind_cost_factor * 0.30, 2)

        return IrreversibilityRiskResult(
            case_version_id=case_version_id,
            option_code=option_code.strip(),
            reversibility_class=rev_class,
            precautionary_risk_score=min(1.0, risk_score),
            unwind_time_months=unwind_time_months,
            unwind_cost_factor=round(unwind_cost_factor, 2),
            risk_summary=risk_summary.strip(),
        )
