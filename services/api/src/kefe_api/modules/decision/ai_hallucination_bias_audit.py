from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AiAuditStatus(StrEnum):
    AUDIT_VERIFIED_GROUNDED = "AUDIT_VERIFIED_GROUNDED"
    POTENTIAL_HALLUCINATION_FLAG = "POTENTIAL_HALLUCINATION_FLAG"
    ASYMMETRIC_BIAS_SKEW = "ASYMMETRIC_BIAS_SKEW"


@dataclass(frozen=True, slots=True)
class AiAuditResult:
    audit_id: str
    target_artifact_id: str
    status: AiAuditStatus
    grounding_confidence_score: float
    bias_asymmetry_index: float
    audit_findings_summary: str


class AiHallucinationBiasAuditService:
    @staticmethod
    def audit_artifact(
        *,
        audit_id: str,
        target_artifact_id: str,
        grounding_confidence_score: float,
        bias_asymmetry_index: float,
        audit_findings_summary: str,
    ) -> AiAuditResult:
        if not 0.0 <= grounding_confidence_score <= 1.0:
            raise ValueError(f"grounding_confidence_score must be in [0.0, 1.0], got {grounding_confidence_score}")
        if not 0.0 <= bias_asymmetry_index <= 1.0:
            raise ValueError(f"bias_asymmetry_index must be in [0.0, 1.0], got {bias_asymmetry_index}")
        if len(audit_findings_summary.strip()) < 10:
            raise ValueError("audit_findings_summary must have at least 10 characters")

        if grounding_confidence_score < 0.70:
            status = AiAuditStatus.POTENTIAL_HALLUCINATION_FLAG
        elif bias_asymmetry_index > 0.35:
            status = AiAuditStatus.ASYMMETRIC_BIAS_SKEW
        else:
            status = AiAuditStatus.AUDIT_VERIFIED_GROUNDED

        return AiAuditResult(
            audit_id=audit_id.strip(),
            target_artifact_id=target_artifact_id.strip(),
            status=status,
            grounding_confidence_score=round(grounding_confidence_score, 2),
            bias_asymmetry_index=round(bias_asymmetry_index, 2),
            audit_findings_summary=audit_findings_summary.strip(),
        )
