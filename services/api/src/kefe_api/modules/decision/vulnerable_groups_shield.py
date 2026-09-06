from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class VulnerableCohort(StrEnum):
    CHILDREN_YOUTH = "CHILDREN_YOUTH"
    ELDERLY_GERIATRIC = "ELDERLY_GERIATRIC"
    LOW_INCOME_IMPOVERISHED = "LOW_INCOME_IMPOVERISHED"
    PERSONS_WITH_DISABILITIES = "PERSONS_WITH_DISABILITIES"
    MINORITY_MARGINALIZED = "MINORITY_MARGINALIZED"


class ProtectionStatus(StrEnum):
    STRONG_PROTECTIVE_FLOOR = "STRONG_PROTECTIVE_FLOOR"
    NEUTRAL_NO_DISPROPORTION = "NEUTRAL_NO_DISPROPORTION"
    SEVERE_DISPROPORTIONATE_BURDEN = "SEVERE_DISPROPORTIONATE_BURDEN"


@dataclass(frozen=True, slots=True)
class CohortEvaluationItem:
    cohort: VulnerableCohort
    impact_score: float
    assessment: str


@dataclass(frozen=True, slots=True)
class VulnerableGroupsShieldResult:
    case_version_id: UUID
    option_code: str
    overall_protection_status: ProtectionStatus
    safety_net_floor_score: float
    cohort_evaluations: tuple[CohortEvaluationItem, ...]


class VulnerableGroupsShieldCalculator:
    @staticmethod
    def audit(
        *,
        case_version_id: UUID,
        option_code: str,
        cohort_evaluations: list[CohortEvaluationItem],
    ) -> VulnerableGroupsShieldResult:
        if not cohort_evaluations:
            raise ValueError("cohort_evaluations must not be empty")

        for item in cohort_evaluations:
            if not -1.0 <= item.impact_score <= 1.0:
                raise ValueError(f"impact_score for {item.cohort} must be in [-1.0, 1.0]")

        # Rawlsian Maximin rule: Find worst-off score among cohorts
        worst_score = min(item.impact_score for item in cohort_evaluations)
        avg_score = sum(item.impact_score for item in cohort_evaluations) / len(cohort_evaluations)

        # Normalize safety net floor score to [0.0, 1.0]
        # (A negative score significantly pulls down the safety floor)
        safety_floor = max(0.0, min(1.0, round(0.50 + (worst_score * 0.50), 2)))

        if worst_score <= -0.40:
            status = ProtectionStatus.SEVERE_DISPROPORTIONATE_BURDEN
        elif avg_score >= 0.30 and worst_score >= 0.0:
            status = ProtectionStatus.STRONG_PROTECTIVE_FLOOR
        else:
            status = ProtectionStatus.NEUTRAL_NO_DISPROPORTION

        return VulnerableGroupsShieldResult(
            case_version_id=case_version_id,
            option_code=option_code.strip(),
            overall_protection_status=status,
            safety_net_floor_score=safety_floor,
            cohort_evaluations=tuple(cohort_evaluations),
        )
