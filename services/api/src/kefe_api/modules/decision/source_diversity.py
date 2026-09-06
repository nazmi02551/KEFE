from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import UUID


class SourcePluralityCategory(StrEnum):
    ACADEMIC_SCIENTIFIC = "ACADEMIC_SCIENTIFIC"
    OFFICIAL_GOVERNMENT = "OFFICIAL_GOVERNMENT"
    CIVIC_INDEPENDENT = "CIVIC_INDEPENDENT"
    MAINSTREAM_JOURNALISM = "MAINSTREAM_JOURNALISM"
    TECHNICAL_INDUSTRY = "TECHNICAL_INDUSTRY"


class DiversityLevel(StrEnum):
    HIGH_DIVERSITY = "HIGH_DIVERSITY"
    BALANCED_DIVERSITY = "BALANCED_DIVERSITY"
    LIMITED_DIVERSITY = "LIMITED_DIVERSITY"


@dataclass(frozen=True, slots=True)
class SourceCategoryBreakdown:
    category: SourcePluralityCategory
    count: int
    percentage: float


@dataclass(frozen=True, slots=True)
class SourceDiversityResult:
    case_version_id: UUID
    total_sources: int
    diversity_level: DiversityLevel
    category_breakdown: tuple[SourceCategoryBreakdown, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_version_id": str(self.case_version_id),
            "total_sources": self.total_sources,
            "diversity_level": self.diversity_level.value,
            "category_breakdown": [
                {
                    "category": b.category.value,
                    "count": b.count,
                    "percentage": b.percentage,
                }
                for b in self.category_breakdown
            ],
        }


class SourceDiversityCalculator:
    @staticmethod
    def calculate(
        case_version_id: UUID,
        source_categories: list[SourcePluralityCategory],
    ) -> SourceDiversityResult:
        if not source_categories:
            raise ValueError("source_categories must not be empty")

        total = len(source_categories)
        counts: dict[SourcePluralityCategory, int] = {}
        for cat in source_categories:
            counts[cat] = counts.get(cat, 0) + 1

        breakdown: list[SourceCategoryBreakdown] = []
        for cat, cnt in counts.items():
            pct = round((cnt / total) * 100.0, 1)
            breakdown.append(
                SourceCategoryBreakdown(
                    category=cat,
                    count=cnt,
                    percentage=pct,
                )
            )

        breakdown.sort(key=lambda x: x.count, reverse=True)
        unique_categories = len(counts)

        # Classification logic based on category dispersion
        if unique_categories >= 3 and breakdown[0].percentage <= 50.0:
            level = DiversityLevel.HIGH_DIVERSITY
        elif unique_categories >= 2:
            level = DiversityLevel.BALANCED_DIVERSITY
        else:
            level = DiversityLevel.LIMITED_DIVERSITY

        return SourceDiversityResult(
            case_version_id=case_version_id,
            total_sources=total,
            diversity_level=level,
            category_breakdown=tuple(breakdown),
        )
