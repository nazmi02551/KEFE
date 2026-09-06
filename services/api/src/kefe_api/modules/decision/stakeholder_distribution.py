from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Mapping, Sequence


class StakeholderCategory(StrEnum):
    DIRECTLY_IMPACTED = "DIRECTLY_IMPACTED"
    FRONTLINE_PRACTITIONERS = "FRONTLINE_PRACTITIONERS"
    COMMERCIAL_ENTERPRISES = "COMMERCIAL_ENTERPRISES"
    REGULATORY_OVERSIGHT = "REGULATORY_OVERSIGHT"
    CIVIC_COMMUNITY = "CIVIC_COMMUNITY"


@dataclass(frozen=True, slots=True)
class StakeholderDistributionItem:
    category: StakeholderCategory
    name: str
    participant_count: int
    sample_share: float
    option_shares: dict[str, float]
    primary_choice: str
    cohesion_index: float
    divergence_from_overall_points: int

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "name": self.name,
            "participant_count": self.participant_count,
            "sample_share": self.sample_share,
            "option_shares": self.option_shares,
            "primary_choice": self.primary_choice,
            "cohesion_index": self.cohesion_index,
            "divergence_from_overall_points": self.divergence_from_overall_points,
        }


@dataclass(frozen=True, slots=True)
class StakeholderDistributionResult:
    case_version_id: str
    total_stakeholders_represented: int
    active_categories_count: int
    stakeholder_distributions: list[StakeholderDistributionItem]
    pluralism_score: float
    generated_at: str

    def to_dict(self) -> dict:
        return {
            "case_version_id": self.case_version_id,
            "total_stakeholders_represented": self.total_stakeholders_represented,
            "active_categories_count": self.active_categories_count,
            "stakeholder_distributions": [s.to_dict() for s in self.stakeholder_distributions],
            "pluralism_score": self.pluralism_score,
            "generated_at": self.generated_at,
        }


class StakeholderDistributionService:
    @staticmethod
    def calculate_cohesion(shares: Mapping[str, float]) -> float:
        if not shares:
            return 0.0
        # Herfindahl-Hirschman index normalized for N options: H = sum(s_i^2)
        hhi = sum(v * v for v in shares.values())
        return round(min(1.0, max(0.0, hhi)), 3)

    @classmethod
    def get_stakeholder_distribution(cls, case_version_id: str) -> StakeholderDistributionResult:
        overall_target_a = 0.52

        items_spec = [
            (
                StakeholderCategory.DIRECTLY_IMPACTED,
                "Doğrudan Etkilenen Yurttaşlar",
                210,
                {"A": 0.68, "B": 0.32},
            ),
            (
                StakeholderCategory.FRONTLINE_PRACTITIONERS,
                "Saha ve Hizmet Uygulayıcıları",
                145,
                {"A": 0.44, "B": 0.56},
            ),
            (
                StakeholderCategory.COMMERCIAL_ENTERPRISES,
                "Sektörel ve Ticari İşletmeler",
                95,
                {"A": 0.35, "B": 0.65},
            ),
            (
                StakeholderCategory.REGULATORY_OVERSIGHT,
                "Denetleyici Kamu ve Hukuk Kurumları",
                60,
                {"A": 0.55, "B": 0.45},
            ),
            (
                StakeholderCategory.CIVIC_COMMUNITY,
                "Geniş Toplum ve Gelecek Kuşaklar",
                380,
                {"A": 0.51, "B": 0.49},
            ),
        ]

        total_participants = sum(count for _, _, count, _ in items_spec)

        distributions: list[StakeholderDistributionItem] = []
        for cat, name, count, shares in items_spec:
            sample_share = round(count / total_participants, 3)
            primary = max(shares.items(), key=lambda x: x[1])[0]
            cohesion = cls.calculate_cohesion(shares)
            divergence = round((shares.get("A", 0.0) - overall_target_a) * 100)

            distributions.append(
                StakeholderDistributionItem(
                    category=cat,
                    name=name,
                    participant_count=count,
                    sample_share=sample_share,
                    option_shares=shares,
                    primary_choice=primary,
                    cohesion_index=cohesion,
                    divergence_from_overall_points=divergence,
                )
            )

        # Pluralism score measures category balance across the 5 categories
        pluralism = round(1.0 - (max(d.sample_share for d in distributions) - min(d.sample_share for d in distributions)), 3)

        return StakeholderDistributionResult(
            case_version_id=case_version_id,
            total_stakeholders_represented=total_participants,
            active_categories_count=len(distributions),
            stakeholder_distributions=distributions,
            pluralism_score=pluralism,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
