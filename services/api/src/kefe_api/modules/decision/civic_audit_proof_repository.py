from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AuditVerificationStatus(StrEnum):
    PEER_ATTESTED_CORROBORATED = "PEER_ATTESTED_CORROBORATED"
    OPEN_EVIDENTIARY_CHALLENGE = "OPEN_EVIDENTIARY_CHALLENGE"
    PENDING_WITNESS_CONFIRMATION = "PENDING_WITNESS_CONFIRMATION"


@dataclass(frozen=True, slots=True)
class CivicAuditReportResult:
    report_id: str
    investigation_title: str
    verification_status: AuditVerificationStatus
    peer_attestation_signatures_count: int
    evidentiary_rigor_score: float
    content_hash_digest: str


class CivicAuditProofRepositoryService:
    @staticmethod
    def publish_report(
        *,
        report_id: str,
        investigation_title: str,
        peer_attestation_signatures_count: int,
        evidentiary_rigor_score: float,
        content_hash_digest: str,
    ) -> CivicAuditReportResult:
        if peer_attestation_signatures_count < 0:
            raise ValueError("peer_attestation_signatures_count cannot be negative")
        if not 0.0 <= evidentiary_rigor_score <= 1.0:
            raise ValueError(f"evidentiary_rigor_score must be in [0.0, 1.0], got {evidentiary_rigor_score}")
        if len(investigation_title.strip()) < 6:
            raise ValueError("investigation_title must have at least 6 characters")
        if len(content_hash_digest.strip()) < 16:
            raise ValueError("content_hash_digest must have at least 16 characters")

        if peer_attestation_signatures_count >= 3 and evidentiary_rigor_score >= 0.85:
            status = AuditVerificationStatus.PEER_ATTESTED_CORROBORATED
        elif peer_attestation_signatures_count >= 1:
            status = AuditVerificationStatus.OPEN_EVIDENTIARY_CHALLENGE
        else:
            status = AuditVerificationStatus.PENDING_WITNESS_CONFIRMATION

        return CivicAuditReportResult(
            report_id=report_id.strip(),
            investigation_title=investigation_title.strip(),
            verification_status=status,
            peer_attestation_signatures_count=peer_attestation_signatures_count,
            evidentiary_rigor_score=round(evidentiary_rigor_score, 2),
            content_hash_digest=content_hash_digest.strip(),
        )
