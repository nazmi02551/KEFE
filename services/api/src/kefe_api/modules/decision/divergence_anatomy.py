from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class DivergenceDriverType(StrEnum):
    NORMATIVE_VALUE_WEIGHT = "NORMATIVE_VALUE_WEIGHT"
    FACTUAL_PROBABILITY_ASSESSMENT = "FACTUAL_PROBABILITY_ASSESSMENT"
    PROCEDURAL_GOVERNANCE = "PROCEDURAL_GOVERNANCE"
    TIME_HORIZON = "TIME_HORIZON"


@dataclass(frozen=True, slots=True)
class DivergenceDriverItem:
    driver_type: DivergenceDriverType
    share_percentage: float
    explanation: str


@dataclass(frozen=True, slots=True)
class DivergenceAnatomyResult:
    case_version_id: UUID
    primary_driver: DivergenceDriverType
    drivers: tuple[DivergenceDriverItem, ...]


class DivergenceAnatomyCalculator:
    @staticmethod
    def calculate(
        case_version_id: UUID,
        driver_inputs: list[dict[str, any]],
    ) -> DivergenceAnatomyResult:
        if not driver_inputs:
            raise ValueError("driver_inputs must not be empty")

        total_weight = sum(float(d.get("weight", 0.0)) for d in driver_inputs)
        base = max(0.001, total_weight)

        drivers: list[DivergenceDriverItem] = []
        for d in driver_inputs:
            w = float(d.get("weight", 0.0))
            pct = round((w / base) * 100.0, 2)
            drivers.append(
                DivergenceDriverItem(
                    driver_type=DivergenceDriverType(d["driver_type"]),
                    share_percentage=pct,
                    explanation=str(d.get("explanation", "")).strip(),
                )
            )

        drivers.sort(key=lambda x: x.share_percentage, reverse=True)
        primary = drivers[0].driver_type

        return DivergenceAnatomyResult(
            case_version_id=case_version_id,
            primary_driver=primary,
            drivers=tuple(drivers),
        )
