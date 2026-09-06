from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PromiseRealizationStatus(StrEnum):
    PROMISE_DELIVERED_VERIFIED = "PROMISE_DELIVERED_VERIFIED"
    IN_PROGRESS_ON_TRACK = "IN_PROGRESS_ON_TRACK"
    PROMISE_BROKEN_DEFAULT = "PROMISE_BROKEN_DEFAULT"


@dataclass(frozen=True, slots=True)
class PromiseOutcomeResult:
    matrix_id: str
    institution_name: str
    promise_title: str
    realization_status: PromiseRealizationStatus
    milestone_completion_pct: float
    empirical_evidence_artifacts_count: int


class InstitutionalPromiseOutcomeMatrixService:
    @staticmethod
    def audit_promise(
        *,
        matrix_id: str,
        institution_name: str,
        promise_title: str,
        milestone_completion_pct: float,
        empirical_evidence_artifacts_count: int,
    ) -> PromiseOutcomeResult:
        if not 0.0 <= milestone_completion_pct <= 1.0:
            raise ValueError(f"milestone_completion_pct must be in [0.0, 1.0], got {milestone_completion_pct}")
        if empirical_evidence_artifacts_count < 0:
            raise ValueError("empirical_evidence_artifacts_count cannot be negative")
        if len(institution_name.strip()) < 3:
            raise ValueError("institution_name must have at least 3 characters")
        if len(promise_title.strip()) < 6:
            raise ValueError("promise_title must have at least 6 characters")

        if milestone_completion_pct >= 0.95 and empirical_evidence_artifacts_count >= 1:
            status = PromiseRealizationStatus.PROMISE_DELIVERED_VERIFIED
        elif milestone_completion_pct >= 0.20:
            status = PromiseRealizationStatus.IN_PROGRESS_ON_TRACK
        else:
            status = PromiseRealizationStatus.PROMISE_BROKEN_DEFAULT

        return PromiseOutcomeResult(
            matrix_id=matrix_id.strip(),
            institution_name=institution_name.strip(),
            promise_title=promise_title.strip(),
            realization_status=status,
            milestone_completion_pct=round(milestone_completion_pct, 2),
            empirical_evidence_artifacts_count=empirical_evidence_artifacts_count,
        )
