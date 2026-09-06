from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class SimilarityAlignmentTier(StrEnum):
    HIGH_TOPOLOGICAL_ANALOGUE = "HIGH_TOPOLOGICAL_ANALOGUE"
    PARTIAL_DOMAIN_OVERLAP = "PARTIAL_DOMAIN_OVERLAP"
    DISTANT_PRECEDENT = "DISTANT_PRECEDENT"


@dataclass(frozen=True, slots=True)
class CrossCaseSimilarityResult:
    source_case_id: UUID
    target_case_id: UUID
    target_case_title: str
    similarity_score: float
    alignment_tier: SimilarityAlignmentTier
    shared_tension_summary: str


class CrossCaseSimilarityCalculator:
    @staticmethod
    def calculate_similarity(
        *,
        source_case_id: UUID,
        target_case_id: UUID,
        target_case_title: str,
        similarity_score: float,
        shared_tension_summary: str,
    ) -> CrossCaseSimilarityResult:
        if len(target_case_title.strip()) < 5:
            raise ValueError("target_case_title must have at least 5 characters")
        if not 0.0 <= similarity_score <= 1.0:
            raise ValueError(f"similarity_score must be in [0.0, 1.0], got {similarity_score}")
        if len(shared_tension_summary.strip()) < 10:
            raise ValueError("shared_tension_summary must have at least 10 characters")

        if similarity_score >= 0.80:
            tier = SimilarityAlignmentTier.HIGH_TOPOLOGICAL_ANALOGUE
        elif similarity_score >= 0.50:
            tier = SimilarityAlignmentTier.PARTIAL_DOMAIN_OVERLAP
        else:
            tier = SimilarityAlignmentTier.DISTANT_PRECEDENT

        return CrossCaseSimilarityResult(
            source_case_id=source_case_id,
            target_case_id=target_case_id,
            target_case_title=target_case_title.strip(),
            similarity_score=round(similarity_score, 2),
            alignment_tier=tier,
            shared_tension_summary=shared_tension_summary.strip(),
        )
