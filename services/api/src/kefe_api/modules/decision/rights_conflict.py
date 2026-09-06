from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class RightsCollisionType(StrEnum):
    PRIVACY_VS_SECURITY = "PRIVACY_VS_SECURITY"
    EXPRESSION_VS_DIGNITY = "EXPRESSION_VS_DIGNITY"
    PROPERTY_VS_ENVIRONMENT = "PROPERTY_VS_ENVIRONMENT"
    INDIVIDUAL_LIBERTY_VS_PUBLIC_HEALTH = "INDIVIDUAL_LIBERTY_VS_PUBLIC_HEALTH"


class RestrictionSeverity(StrEnum):
    PERMISSIBLE_RESTRICTION = "PERMISSIBLE_RESTRICTION"
    CORE_RIGHT_EROSION = "CORE_RIGHT_EROSION"
    UNCONSTITUTIONAL_BREACH = "UNCONSTITUTIONAL_BREACH"


@dataclass(frozen=True, slots=True)
class RightsConflictResult:
    case_version_id: UUID
    option_code: str
    collision_type: RightsCollisionType
    severity: RestrictionSeverity
    inalienable_core_score: float
    constitutional_rationale: str


class RightsConflictCalculator:
    @staticmethod
    def evaluate(
        *,
        case_version_id: UUID,
        option_code: str,
        collision_type: RightsCollisionType,
        inalienable_core_score: float,
        constitutional_rationale: str,
    ) -> RightsConflictResult:
        if not 0.0 <= inalienable_core_score <= 1.0:
            raise ValueError(f"inalienable_core_score must be in [0.0, 1.0], got {inalienable_core_score}")
        if len(constitutional_rationale.strip()) < 10:
            raise ValueError("constitutional_rationale must have at least 10 characters")

        # Determine constitutional severity based on how well core essence is preserved
        if inalienable_core_score >= 0.70:
            severity = RestrictionSeverity.PERMISSIBLE_RESTRICTION
        elif inalienable_core_score >= 0.40:
            severity = RestrictionSeverity.CORE_RIGHT_EROSION
        else:
            severity = RestrictionSeverity.UNCONSTITUTIONAL_BREACH

        return RightsConflictResult(
            case_version_id=case_version_id,
            option_code=option_code.strip(),
            collision_type=collision_type,
            severity=severity,
            inalienable_core_score=round(inalienable_core_score, 2),
            constitutional_rationale=constitutional_rationale.strip(),
        )
