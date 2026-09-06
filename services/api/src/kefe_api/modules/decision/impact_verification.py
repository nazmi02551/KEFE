from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OutcomeVerdict(StrEnum):
    FULL_RESOLUTION = "FULL_RESOLUTION"
    SUBSTANTIAL_PROGRESS = "SUBSTANTIAL_PROGRESS"
    PARTIAL_SYMBOLIC_ONLY = "PARTIAL_SYMBOLIC_ONLY"
    REJECTED_NON_COMPLIANT = "REJECTED_NON_COMPLIANT"


@dataclass(frozen=True, slots=True)
class ImpactVerificationResult:
    verification_id: str
    action_id: str
    outcome_verdict: OutcomeVerdict
    resolution_score: float
    auditor_consensus_count: int
    verification_notes: str


class ImpactVerificationEngine:
    @staticmethod
    def evaluate(
        *,
        verification_id: str,
        action_id: str,
        outcome_verdict: OutcomeVerdict,
        resolution_score: float,
        auditor_consensus_count: int,
        verification_notes: str,
    ) -> ImpactVerificationResult:
        if not 0.0 <= resolution_score <= 1.0:
            raise ValueError(f"resolution_score must be in [0.0, 1.0], got {resolution_score}")
        if auditor_consensus_count < 1:
            raise ValueError("auditor_consensus_count must be at least 1")
        if len(verification_notes.strip()) < 5:
            raise ValueError("verification_notes must have at least 5 characters")

        return ImpactVerificationResult(
            verification_id=verification_id.strip(),
            action_id=action_id.strip(),
            outcome_verdict=outcome_verdict,
            resolution_score=round(resolution_score, 2),
            auditor_consensus_count=auditor_consensus_count,
            verification_notes=verification_notes.strip(),
        )
