from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class StakeholderGroupType(StrEnum):
    DIRECT_USERS = "DIRECT_USERS"
    WORKERS = "WORKERS"
    VULNERABLE_GROUPS = "VULNERABLE_GROUPS"
    TAXPAYERS = "TAXPAYERS"
    FUTURE_GENERATIONS = "FUTURE_GENERATIONS"


class StakeholderImpactType(StrEnum):
    BENEFIT = "BENEFIT"
    BURDEN = "BURDEN"
    NEUTRAL = "NEUTRAL"
    PROTECTION = "PROTECTION"


@dataclass(frozen=True, slots=True)
class StakeholderImpactItem:
    stakeholder_group: StakeholderGroupType
    impact_type: StakeholderImpactType
    impact_score: int
    description: str


@dataclass(frozen=True, slots=True)
class StakeholderImpactMatrixResult:
    case_version_id: UUID
    option_code: str
    impact_items: tuple[StakeholderImpactItem, ...]
    net_equity_score: int


class StakeholderImpactCalculator:
    @staticmethod
    def calculate_matrix(
        case_version_id: UUID,
        option_code: str,
        raw_items: list[dict[str, any]],
    ) -> StakeholderImpactMatrixResult:
        items: list[StakeholderImpactItem] = []
        net_score = 0

        for r in raw_items:
            score = max(-5, min(5, int(r.get("impact_score", 0))))
            net_score += score
            items.append(
                StakeholderImpactItem(
                    stakeholder_group=StakeholderGroupType(r["stakeholder_group"]),
                    impact_type=StakeholderImpactType(r["impact_type"]),
                    impact_score=score,
                    description=str(r.get("description", "")).strip(),
                )
            )

        return StakeholderImpactMatrixResult(
            case_version_id=case_version_id,
            option_code=option_code.strip(),
            impact_items=tuple(items),
            net_equity_score=net_score,
        )
