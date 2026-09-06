from __future__ import annotations

from kefe_api.modules.decision.ai_hallucination_bias_audit import (
    AiAuditResult,
    AiAuditStatus,
    AiHallucinationBiasAuditService,
)


def test_ai_audit_verifies_grounding() -> None:
    r = AiHallucinationBiasAuditService.audit_artifact(
        audit_id="adt_001",
        target_artifact_id="art_synth_001",
        grounding_confidence_score=0.96,
        bias_asymmetry_index=0.08,
        audit_findings_summary="Tüm ampirik iddialar birincil kaynaklara dayanıyor; anlamsal tarafsızlık doğrulandı.",
    )

    assert isinstance(r, AiAuditResult)
    assert r.status == AiAuditStatus.AUDIT_VERIFIED_GROUNDED
    assert r.grounding_confidence_score == 0.96
    assert r.bias_asymmetry_index == 0.08


def test_ai_audit_invalid_scores() -> None:
    failed = False
    try:
        AiHallucinationBiasAuditService.audit_artifact(
            audit_id="adt_002",
            target_artifact_id="art_002",
            grounding_confidence_score=1.50,  # > 1.0
            bias_asymmetry_index=-0.1,  # < 0.0
            audit_findings_summary="Kısa",  # < 10
        )
    except ValueError:
        failed = True

    assert failed is True
