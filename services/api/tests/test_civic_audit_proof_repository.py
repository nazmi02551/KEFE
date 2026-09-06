from __future__ import annotations

from kefe_api.modules.decision.civic_audit_proof_repository import (
    AuditVerificationStatus,
    CivicAuditProofRepositoryService,
    CivicAuditReportResult,
)


def test_civic_audit_publishes_corroborated_report() -> None:
    r = CivicAuditProofRepositoryService.publish_report(
        report_id="aud_rep_001",
        investigation_title="İmar Planı Değişikliği ve Yeşil Alan Dönüşüm Raporu",
        peer_attestation_signatures_count=5,
        evidentiary_rigor_score=0.96,
        content_hash_digest="sha256:4a8b7c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b",
    )

    assert isinstance(r, CivicAuditReportResult)
    assert r.verification_status == AuditVerificationStatus.PEER_ATTESTED_CORROBORATED
    assert r.peer_attestation_signatures_count == 5
    assert r.evidentiary_rigor_score == 0.96


def test_civic_audit_invalid_inputs() -> None:
    failed = False
    try:
        CivicAuditProofRepositoryService.publish_report(
            report_id="aud_002",
            investigation_title="Kısa",  # < 6
            peer_attestation_signatures_count=-1,  # < 0
            evidentiary_rigor_score=1.50,  # > 1.0
            content_hash_digest="kısa_hash",  # < 16
        )
    except ValueError:
        failed = True

    assert failed is True
