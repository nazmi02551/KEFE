from __future__ import annotations

from kefe_api.modules.decision.institutional_promise_outcome_matrix import (
    InstitutionalPromiseOutcomeMatrixService,
    PromiseOutcomeResult,
    PromiseRealizationStatus,
)


def test_promise_outcome_verifies_delivered_milestone() -> None:
    r = InstitutionalPromiseOutcomeMatrixService.audit_promise(
        matrix_id="mtx_001",
        institution_name="İBB Raylı Sistemler Dairesi",
        promise_title="Ümraniye-Ataşehir-Göztepe Metro Hattı 1. Etap Açılışı",
        milestone_completion_pct=1.00,
        empirical_evidence_artifacts_count=4,
    )

    assert isinstance(r, PromiseOutcomeResult)
    assert r.realization_status == PromiseRealizationStatus.PROMISE_DELIVERED_VERIFIED
    assert r.milestone_completion_pct == 1.00
    assert r.empirical_evidence_artifacts_count == 4


def test_promise_outcome_invalid_inputs() -> None:
    failed = False
    try:
        InstitutionalPromiseOutcomeMatrixService.audit_promise(
            matrix_id="mtx_002",
            institution_name="AB",  # < 3
            promise_title="Kısa",  # < 6
            milestone_completion_pct=1.50,  # > 1.0
            empirical_evidence_artifacts_count=-1,  # < 0
        )
    except ValueError:
        failed = True

    assert failed is True
