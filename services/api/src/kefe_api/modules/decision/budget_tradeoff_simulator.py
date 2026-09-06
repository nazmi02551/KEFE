from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class TradeoffProfile(StrEnum):
    HEALTH_EDUCATION_PRIORITY = "HEALTH_EDUCATION_PRIORITY"
    INFRASTRUCTURE_GROWTH = "INFRASTRUCTURE_GROWTH"
    ECOLOGICAL_TRANSITION = "ECOLOGICAL_TRANSITION"
    BALANCED_ALLOCATION = "BALANCED_ALLOCATION"


@dataclass(frozen=True, slots=True)
class BudgetTradeoffResult:
    tradeoff_id: str
    case_version_id: UUID
    healthcare_pct: int
    education_pct: int
    infrastructure_pct: int
    green_transition_pct: int
    unallocated_pct: int
    tradeoff_profile: TradeoffProfile


class BudgetTradeoffSimulator:
    @staticmethod
    def evaluate(
        *,
        tradeoff_id: str,
        case_version_id: UUID,
        healthcare_pct: int,
        education_pct: int,
        infrastructure_pct: int,
        green_transition_pct: int,
    ) -> BudgetTradeoffResult:
        for val, name in [
            (healthcare_pct, "healthcare_pct"),
            (education_pct, "education_pct"),
            (infrastructure_pct, "infrastructure_pct"),
            (green_transition_pct, "green_transition_pct"),
        ]:
            if not 0 <= val <= 100:
                raise ValueError(f"{name} must be in [0, 100], got {val}")

        total = healthcare_pct + education_pct + infrastructure_pct + green_transition_pct
        if total > 100:
            raise ValueError(f"Total budget allocation cannot exceed 100%, got {total}%")

        unallocated = 100 - total

        if healthcare_pct + education_pct >= 55:
            profile = TradeoffProfile.HEALTH_EDUCATION_PRIORITY
        elif infrastructure_pct >= 40:
            profile = TradeoffProfile.INFRASTRUCTURE_GROWTH
        elif green_transition_pct >= 40:
            profile = TradeoffProfile.ECOLOGICAL_TRANSITION
        else:
            profile = TradeoffProfile.BALANCED_ALLOCATION

        return BudgetTradeoffResult(
            tradeoff_id=tradeoff_id.strip(),
            case_version_id=case_version_id,
            healthcare_pct=healthcare_pct,
            education_pct=education_pct,
            infrastructure_pct=infrastructure_pct,
            green_transition_pct=green_transition_pct,
            unallocated_pct=unallocated,
            tradeoff_profile=profile,
        )
