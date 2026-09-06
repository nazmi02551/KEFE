from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class DominantMoralAttractor(StrEnum):
    UTILITARIAN_WELFARE = "UTILITARIAN_WELFARE"
    DEONTOLOGICAL_RIGHTS = "DEONTOLOGICAL_RIGHTS"
    COMMUNITARIAN_SOLIDARITY = "COMMUNITARIAN_SOLIDARITY"
    INTERGENERATIONAL_CARE = "INTERGENERATIONAL_CARE"


@dataclass(frozen=True, slots=True)
class EthicalVectorSpaceResult:
    case_version_id: UUID
    utilitarian_weight: float
    deontological_weight: float
    communitarian_weight: float
    intergenerational_weight: float
    dominant_attractor: DominantMoralAttractor


class EthicalVectorSpaceCalculator:
    @staticmethod
    def calculate_vector(
        *,
        case_version_id: UUID,
        utilitarian_score: float,
        deontological_score: float,
        communitarian_score: float,
        intergenerational_score: float,
    ) -> EthicalVectorSpaceResult:
        coords = {
            DominantMoralAttractor.UTILITARIAN_WELFARE: utilitarian_score,
            DominantMoralAttractor.DEONTOLOGICAL_RIGHTS: deontological_score,
            DominantMoralAttractor.COMMUNITARIAN_SOLIDARITY: communitarian_score,
            DominantMoralAttractor.INTERGENERATIONAL_CARE: intergenerational_score,
        }

        for k, v in coords.items():
            if not 0.0 <= v <= 1.0:
                raise ValueError(f"{k} must be in [0.0, 1.0], got {v}")

        # Find dominant coordinate
        dominant = max(coords.items(), key=lambda x: x[1])[0]

        return EthicalVectorSpaceResult(
            case_version_id=case_version_id,
            utilitarian_weight=round(utilitarian_score, 2),
            deontological_weight=round(deontological_score, 2),
            communitarian_weight=round(communitarian_score, 2),
            intergenerational_weight=round(intergenerational_score, 2),
            dominant_attractor=dominant,
        )
