from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ProportionalityOutcome(StrEnum):
    PROPORTIONAL_VALID = "PROPORTIONAL_VALID"
    EXCESSIVELY_BURDENSOME = "EXCESSIVELY_BURDENSOME"
    DISPROPORTIONATE_INVALID = "DISPROPORTIONATE_INVALID"


@dataclass(frozen=True, slots=True)
class ProportionalityTestResult:
    case_version_id: UUID
    option_code: str
    composite_proportionality_score: float
    outcome: ProportionalityOutcome
    suitability_score: float
    necessity_least_intrusive_score: float
    strict_proportionality_score: float
    summary: str


class ProportionalityCalculator:
    @staticmethod
    def evaluate(
        *,
        case_version_id: UUID,
        option_code: str,
        suitability_score: float,
        necessity_least_intrusive_score: float,
        strict_proportionality_score: float,
        summary: str,
    ) -> ProportionalityTestResult:
        for name, val in [
            ("suitability_score", suitability_score),
            ("necessity_least_intrusive_score", necessity_least_intrusive_score),
            ("strict_proportionality_score", strict_proportionality_score),
        ]:
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"{name} must be in [0.0, 1.0], got {val}")

        if len(summary.strip()) < 10:
            raise ValueError("summary must have at least 10 characters")

        # Weighted calculation: Suitability (30%), Least Intrusive (40%), Strict Proportionality (30%)
        composite = round(
            (suitability_score * 0.30)
            + (necessity_least_intrusive_score * 0.40)
            + (strict_proportionality_score * 0.30),
            2,
        )

        if composite >= 0.70 and necessity_least_intrusive_score >= 0.60:
            outcome = ProportionalityOutcome.PROPORTIONAL_VALID
        elif composite >= 0.40:
            outcome = ProportionalityOutcome.EXCESSIVELY_BURDENSOME
        else:
            outcome = ProportionalityOutcome.DISPROPORTIONATE_INVALID

        return ProportionalityTestResult(
            case_version_id=case_version_id,
            option_code=option_code.strip(),
            composite_proportionality_score=composite,
            outcome=outcome,
            suitability_score=round(suitability_score, 2),
            necessity_least_intrusive_score=round(necessity_least_intrusive_score, 2),
            strict_proportionality_score=round(strict_proportionality_score, 2),
            summary=summary.strip(),
        )
