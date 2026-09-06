from __future__ import annotations

from kefe_api.modules.decision.multi_llm_consensus import (
    ModelAgreementLevel,
    MultiLlmConsensusResult,
    MultiLlmConsensusService,
)


def test_multi_llm_achieves_unanimous_consensus() -> None:
    r = MultiLlmConsensusService.evaluate_consensus(
        consensus_id="mlm_001",
        prompt_context_hash="hash_prompt_001",
        models_evaluated_count=4,
        semantic_convergence_score=0.95,
        synthesized_consensus_output="Tüm modeller karbon salınım vergilendirmesinin kamu gelirine etkisinde anlaştı.",
    )

    assert isinstance(r, MultiLlmConsensusResult)
    assert r.agreement_level == ModelAgreementLevel.UNANIMOUS_CROSS_MODEL_CONSENSUS
    assert r.models_evaluated_count == 4
    assert r.semantic_convergence_score == 0.95


def test_multi_llm_invalid_models_count() -> None:
    failed = False
    try:
        MultiLlmConsensusService.evaluate_consensus(
            consensus_id="mlm_002",
            prompt_context_hash="hash_002",
            models_evaluated_count=2,  # < 3
            semantic_convergence_score=1.50,  # > 1.0
            synthesized_consensus_output="Kısa",  # < 10
        )
    except ValueError:
        failed = True

    assert failed is True
