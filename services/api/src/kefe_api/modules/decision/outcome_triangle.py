from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class TriangleArchetype(StrEnum):
    RIGHTS_CENTRIC = "RIGHTS_CENTRIC"
    EMPATHY_CENTRIC = "EMPATHY_CENTRIC"
    UTILITY_CENTRIC = "UTILITY_CENTRIC"
    TRI_BALANCED_HARMONY = "TRI_BALANCED_HARMONY"


@dataclass(frozen=True, slots=True)
class OutcomeTriangleResult:
    case_version_id: UUID
    option_code: str
    rules_weight: float
    empathy_weight: float
    utility_weight: float
    dominant_archetype: TriangleArchetype


class OutcomeTriangleCalculator:
    @staticmethod
    def calculate_balance(
        *,
        case_version_id: UUID,
        option_code: str,
        rules_score: float,
        empathy_score: float,
        utility_score: float,
    ) -> OutcomeTriangleResult:
        r = max(0.0, float(rules_score))
        e = max(0.0, float(empathy_score))
        u = max(0.0, float(utility_score))

        total = r + e + u
        if total <= 0.0001:
            r_w, e_w, u_w = 0.3333, 0.3333, 0.3334
        else:
            r_w = round(r / total, 4)
            e_w = round(e / total, 4)
            u_w = round(1.0 - (r_w + e_w), 4)

        if r_w >= 0.50:
            archetype = TriangleArchetype.RIGHTS_CENTRIC
        elif e_w >= 0.50:
            archetype = TriangleArchetype.EMPATHY_CENTRIC
        elif u_w >= 0.50:
            archetype = TriangleArchetype.UTILITY_CENTRIC
        else:
            archetype = TriangleArchetype.TRI_BALANCED_HARMONY

        return OutcomeTriangleResult(
            case_version_id=case_version_id,
            option_code=option_code.strip(),
            rules_weight=r_w,
            empathy_weight=e_w,
            utility_weight=u_w,
            dominant_archetype=archetype,
        )
