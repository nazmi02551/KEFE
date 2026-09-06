from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib


class ImpactEvidenceType(StrEnum):
    OFFICIAL_GAZETTE_DECREE = "OFFICIAL_GAZETTE_DECREE"
    AUDIT_EXPENDITURE_RECEIPT = "AUDIT_EXPENDITURE_RECEIPT"
    SENSOR_TELEMETRY_DATA = "SENSOR_TELEMETRY_DATA"
    THIRD_PARTY_ACADEMIC_STUDY = "THIRD_PARTY_ACADEMIC_STUDY"


class EvidenceVerificationStatus(StrEnum):
    PENDING_AUDIT = "PENDING_AUDIT"
    VERIFIED_AUTHENTIC = "VERIFIED_AUTHENTIC"
    CHALLENGED_OR_INSUFFICIENT = "CHALLENGED_OR_INSUFFICIENT"


@dataclass(frozen=True, slots=True)
class ImpactEvidenceResult:
    evidence_id: str
    action_id: str
    evidence_type: ImpactEvidenceType
    evidence_title: str
    source_url: str
    sha256_digest: str
    verification_status: EvidenceVerificationStatus


class ImpactEvidenceService:
    @staticmethod
    def register_evidence(
        *,
        evidence_id: str,
        action_id: str,
        evidence_type: ImpactEvidenceType,
        evidence_title: str,
        source_url: str,
        raw_document_content: str,
        verification_status: EvidenceVerificationStatus = EvidenceVerificationStatus.VERIFIED_AUTHENTIC,
    ) -> ImpactEvidenceResult:
        if len(evidence_title.strip()) < 5:
            raise ValueError("evidence_title must have at least 5 characters")
        if not source_url.startswith("http://") and not source_url.startswith("https://"):
            raise ValueError("source_url must be a valid HTTP(S) URL")
        if len(raw_document_content.strip()) < 10:
            raise ValueError("raw_document_content must have at least 10 characters")

        digest = hashlib.sha256(raw_document_content.encode("utf-8")).hexdigest()

        return ImpactEvidenceResult(
            evidence_id=evidence_id.strip(),
            action_id=action_id.strip(),
            evidence_type=evidence_type,
            evidence_title=evidence_title.strip(),
            source_url=source_url.strip(),
            sha256_digest=digest,
            verification_status=verification_status,
        )
