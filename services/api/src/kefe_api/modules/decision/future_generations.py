from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class TimeHorizon(StrEnum):
    HORIZON_5_YEARS = "HORIZON_5_YEARS"
    HORIZON_20_YEARS = "HORIZON_20_YEARS"
    HORIZON_50_YEARS = "HORIZON_50_YEARS"
    HORIZON_100_YEARS = "HORIZON_100_YEARS"


@dataclass(frozen=True, slots=True)
class HorizonProjectionItem:
    horizon: TimeHorizon
    impact_score: float
    summary: str


@dataclass(frozen=True, slots=True)
class FutureGenerationsResult:
    case_version_id: UUID
    option_code: str
    net_intergenerational_score: float
    projections: tuple[HorizonProjectionItem, ...]


class FutureGenerationsCalculator:
    @staticmethod
    def calculate(
        *,
        case_version_id: UUID,
        option_code: str,
        projections: list[HorizonProjectionItem],
    ) -> FutureGenerationsResult:
        if not projections:
            raise ValueError("Projections list must not be empty")

        for p in projections:
            if not -1.0 <= p.impact_score <= 1.0:
                raise ValueError(f"Impact score for {p.horizon} must be in [-1.0, 1.0]")

        # Weighted intergenerational calculation (long horizons carry equal non-discounted weight)
        net_score = round(sum(p.impact_score for p in projections) / len(projections), 2)

        return FutureGenerationsResult(
            case_version_id=case_version_id,
            option_code=option_code.strip(),
            net_intergenerational_score=net_score,
            projections=tuple(projections),
        )
