from __future__ import annotations

from kefe_api.modules.decision.impact_verification import (
    ImpactVerificationEngine,
    ImpactVerificationResult,
    OutcomeVerdict,
)


def test_impact_verification_engine_evaluates_verdict() -> None:
    r = ImpactVerificationEngine.evaluate(
        verification_id="ver_001",
        action_id="act_001",
        outcome_verdict=OutcomeVerdict.FULL_RESOLUTION,
        resolution_score=0.92,
        auditor_consensus_count=12,
        verification_notes="Bağımsız çevre mühendisleri ve sivil toplum izleme heyeti tarafından atık arıtma tesisi yerinde incelenmiş ve nehir suyu temizliği onaylanmıştır.",
    )

    assert isinstance(r, ImpactVerificationResult)
    assert r.outcome_verdict == OutcomeVerdict.FULL_RESOLUTION
    assert r.resolution_score == 0.92
    assert r.auditor_consensus_count == 12


def test_impact_verification_invalid_consensus() -> None:
    failed = False
    try:
        ImpactVerificationEngine.evaluate(
            verification_id="ver_002",
            action_id="act_001",
            outcome_verdict=OutcomeVerdict.SUBSTANTIAL_PROGRESS,
            resolution_score=0.80,
            auditor_consensus_count=0,  # < 1
            verification_notes="Not",
        )
    except ValueError:
        failed = True

    assert failed is True
