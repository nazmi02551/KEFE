from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReasoningTransparencyTier(StrEnum):
    FULL_AXIOMATIC_PROVENANCE = "FULL_AXIOMATIC_PROVENANCE"
    SIMPLIFIED_CAUSAL_TREE = "SIMPLIFIED_CAUSAL_TREE"
    EVIDENTIARY_WEIGHT_DECOMPOSITION = "EVIDENTIARY_WEIGHT_DECOMPOSITION"


@dataclass(frozen=True, slots=True)
class XaiProvenanceResult:
    provenance_id: str
    target_synthesis_id: str
    transparency_tier: ReasoningTransparencyTier
    causal_steps_count: int
    axiomatic_grounding_score: float
    root_axiom_summary: str


class XaiReasoningProvenanceService:
    @staticmethod
    def generate_provenance_graph(
        *,
        provenance_id: str,
        target_synthesis_id: str,
        causal_steps_count: int,
        axiomatic_grounding_score: float,
        root_axiom_summary: str,
    ) -> XaiProvenanceResult:
        if causal_steps_count < 2:
            raise ValueError(f"causal_steps_count must be at least 2, got {causal_steps_count}")
        if not 0.0 <= axiomatic_grounding_score <= 1.0:
            raise ValueError(f"axiomatic_grounding_score must be in [0.0, 1.0], got {axiomatic_grounding_score}")
        if len(root_axiom_summary.strip()) < 10:
            raise ValueError("root_axiom_summary must have at least 10 characters")

        if axiomatic_grounding_score >= 0.90:
            tier = ReasoningTransparencyTier.FULL_AXIOMATIC_PROVENANCE
        elif axiomatic_grounding_score >= 0.60:
            tier = ReasoningTransparencyTier.SIMPLIFIED_CAUSAL_TREE
        else:
            tier = ReasoningTransparencyTier.EVIDENTIARY_WEIGHT_DECOMPOSITION

        return XaiProvenanceResult(
            provenance_id=provenance_id.strip(),
            target_synthesis_id=target_synthesis_id.strip(),
            transparency_tier=tier,
            causal_steps_count=causal_steps_count,
            axiomatic_grounding_score=round(axiomatic_grounding_score, 2),
            root_axiom_summary=root_axiom_summary.strip(),
        )
