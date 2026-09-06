from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ModelAgreementLevel(StrEnum):
    UNANIMOUS_CROSS_MODEL_CONSENSUS = "UNANIMOUS_CROSS_MODEL_CONSENSUS"
    MAJORITY_CONVERGENT_SYNTHESIS = "MAJORITY_CONVERGENT_SYNTHESIS"
    MODEL_DIVERGENCE_REVIEW_REQUIRED = "MODEL_DIVERGENCE_REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class MultiLlmConsensusResult:
    consensus_id: str
    prompt_context_hash: str
    agreement_level: ModelAgreementLevel
    models_evaluated_count: int
    semantic_convergence_score: float
    synthesized_consensus_output: str


class MultiLlmConsensusService:
    @staticmethod
    def evaluate_consensus(
        *,
        consensus_id: str,
        prompt_context_hash: str,
        models_evaluated_count: int,
        semantic_convergence_score: float,
        synthesized_consensus_output: str,
    ) -> MultiLlmConsensusResult:
        if models_evaluated_count < 3:
            raise ValueError(f"models_evaluated_count must be at least 3, got {models_evaluated_count}")
        if not 0.0 <= semantic_convergence_score <= 1.0:
            raise ValueError(f"semantic_convergence_score must be in [0.0, 1.0], got {semantic_convergence_score}")
        if len(synthesized_consensus_output.strip()) < 10:
            raise ValueError("synthesized_consensus_output must have at least 10 characters")

        if semantic_convergence_score >= 0.90:
            level = ModelAgreementLevel.UNANIMOUS_CROSS_MODEL_CONSENSUS
        elif semantic_convergence_score >= 0.65:
            level = ModelAgreementLevel.MAJORITY_CONVERGENT_SYNTHESIS
        else:
            level = ModelAgreementLevel.MODEL_DIVERGENCE_REVIEW_REQUIRED

        return MultiLlmConsensusResult(
            consensus_id=consensus_id.strip(),
            prompt_context_hash=prompt_context_hash.strip(),
            agreement_level=level,
            models_evaluated_count=models_evaluated_count,
            semantic_convergence_score=round(semantic_convergence_score, 2),
            synthesized_consensus_output=synthesized_consensus_output.strip(),
        )
