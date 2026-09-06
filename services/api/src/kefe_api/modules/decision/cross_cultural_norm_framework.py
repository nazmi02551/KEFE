from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CulturalNormDimension(StrEnum):
    COMMUNITY_SOLIDARITY_AND_MUTUALITY = "COMMUNITY_SOLIDARITY_AND_MUTUALITY"
    INDIVIDUAL_AUTONOMY_AND_LIBERTY = "INDIVIDUAL_AUTONOMY_AND_LIBERTY"
    INTERGENERATIONAL_STEWARDSHIP = "INTERGENERATIONAL_STEWARDSHIP"
    PROCEDURAL_JUSTICE_AND_EQUITY = "PROCEDURAL_JUSTICE_AND_EQUITY"


@dataclass(frozen=True, slots=True)
class CulturalNormResult:
    framework_id: str
    region_identifier: str
    primary_dimension: CulturalNormDimension
    cultural_alignment_score: float
    universal_baseline_compliance: bool
    norm_synthesis_summary: str


class CrossCulturalNormFrameworkService:
    @staticmethod
    def map_norms(
        *,
        framework_id: str,
        region_identifier: str,
        primary_dimension: CulturalNormDimension,
        cultural_alignment_score: float,
        universal_baseline_compliance: bool,
        norm_synthesis_summary: str,
    ) -> CulturalNormResult:
        if len(region_identifier.strip()) < 2:
            raise ValueError("region_identifier must have at least 2 characters")
        if not 0.0 <= cultural_alignment_score <= 1.0:
            raise ValueError(f"cultural_alignment_score must be in [0.0, 1.0], got {cultural_alignment_score}")
        if len(norm_synthesis_summary.strip()) < 10:
            raise ValueError("norm_synthesis_summary must have at least 10 characters")

        return CulturalNormResult(
            framework_id=framework_id.strip(),
            region_identifier=region_identifier.strip(),
            primary_dimension=primary_dimension,
            cultural_alignment_score=round(cultural_alignment_score, 2),
            universal_baseline_compliance=universal_baseline_compliance,
            norm_synthesis_summary=norm_synthesis_summary.strip(),
        )
