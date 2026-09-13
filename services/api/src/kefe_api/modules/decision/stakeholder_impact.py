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

    def to_dict(self) -> dict[str, any]:
        return {
            "stakeholder_group": self.stakeholder_group.value,
            "impact_type": self.impact_type.value,
            "impact_score": self.impact_score,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class StakeholderImpactMatrixResult:
    case_version_id: UUID
    option_code: str
    impact_items: tuple[StakeholderImpactItem, ...]
    net_equity_score: int

    def to_dict(self) -> dict[str, any]:
        return {
            "case_version_id": str(self.case_version_id),
            "option_code": self.option_code,
            "net_equity_score": self.net_equity_score,
            "impact_items": [i.to_dict() for i in self.impact_items],
        }


class StakeholderImpactCalculator:
    @classmethod
    def compute_for_case(
        cls, case_version_id: UUID, option_code: str = "A"
    ) -> StakeholderImpactMatrixResult:
        """Deterministic stakeholder impact matrix and net equity score for a case."""
        raw_items = [
            {
                "stakeholder_group": StakeholderGroupType.DIRECT_USERS.value,
                "impact_type": StakeholderImpactType.BENEFIT.value,
                "impact_score": 4,
                "description": "Doğrudan hizmet erişimi ve kullanıcı refahı artışı.",
            },
            {
                "stakeholder_group": StakeholderGroupType.WORKERS.value,
                "impact_type": StakeholderImpactType.BURDEN.value,
                "impact_score": -2,
                "description": "Çalışanlara operasyonel ve vardiyasal iş yükü transferi.",
            },
            {
                "stakeholder_group": StakeholderGroupType.TAXPAYERS.value,
                "impact_type": StakeholderImpactType.BURDEN.value,
                "impact_score": -1,
                "description": "Kamu finansmanı ve sübvansiyon maliyet payı.",
            },
            {
                "stakeholder_group": StakeholderGroupType.VULNERABLE_GROUPS.value,
                "impact_type": StakeholderImpactType.PROTECTION.value,
                "impact_score": 5,
                "description": "Dezavantajlı kesimlerin hak ve güvenliğinin korunması.",
            },
        ]
        return cls.calculate_matrix(
            case_version_id=case_version_id,
            option_code=option_code,
            raw_items=raw_items,
        )

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

