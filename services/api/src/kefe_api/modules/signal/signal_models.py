from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class SignalQualificationTier(StrEnum):
    GOLD_STANDARD = "GOLD_STANDARD"
    SILVER_VALIDATED = "SILVER_VALIDATED"
    BRONZE_OBSERVED = "BRONZE_OBSERVED"
    UNQUALIFIED = "UNQUALIFIED"


class SignalDispatchStatus(StrEnum):
    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ACTION_PLEDGED = "ACTION_PLEDGED"


@dataclass(frozen=True, slots=True)
class QualifiedSignal:
    """An immutable, append-only qualified signal record.

    Computed from CORE_PRE_RESULT (Commit-First) contributions only.
    A signal snapshot is never mutated in-place; new versions produce
    a new QualifiedSignal with an incremented methodology_version.

    Invariants:
    - sample_size >= 1 (enforced by the qualification engine before storage)
    - case_title, consensus_statement are governed locale strings
    - qualification_tier reflects methodology thresholds at certification time
    - qualification_audit_hash is SHA-256 of canonical input fields
    """

    signal_id: UUID
    case_version_id: UUID
    case_title: str
    consensus_statement: str
    agreement_percentage: float
    sample_size: int
    qualification_tier: SignalQualificationTier
    methodology_version: str
    qualification_audit_hash: str
    certified_at: datetime
    dispatch_status: SignalDispatchStatus = SignalDispatchStatus.PENDING
    dispatched_target_id: UUID | None = None
    dispatched_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.sample_size < 1:
            raise ValueError("sample_size must be >= 1")
        if not (0.0 <= self.agreement_percentage <= 100.0):
            raise ValueError("agreement_percentage must be in [0, 100]")
        if not self.case_title.strip():
            raise ValueError("case_title must not be blank")
        if not self.consensus_statement.strip():
            raise ValueError("consensus_statement must not be blank")


@dataclass(frozen=True, slots=True)
class SignalComputationInput:
    """Aggregated Commit-First pre-result data for a CaseVersion.

    Fetched from the decision/collective_result pipeline.
    Only CORE_PRE_RESULT contribution-class rows are included.
    """

    case_version_id: UUID
    case_title: str
    core_commit_count: int
    top_stance_code: str
    top_stance_count: int
    agreement_percentage: float
    stance_distribution: dict[str, float]
    computed_at: datetime