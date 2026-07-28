from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class ContributionClass(StrEnum):
    CORE_PRE_RESULT = "CORE_PRE_RESULT"
    EXPOSED = "EXPOSED"


class RevisionCommitStatus(StrEnum):
    COMMITTED = "COMMITTED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    NOT_FOUND = "NOT_FOUND"
    ALREADY_COMMITTED = "ALREADY_COMMITTED"
    INCOMPLETE = "INCOMPLETE"
    IDEMPOTENCY_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"


@dataclass(frozen=True, slots=True)
class RevisionDraft:
    session_id: UUID
    flow_step_code: str
    responses: dict[UUID, Any] = field(default_factory=dict)
    reason_snapshot: dict[str, Any] | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class DecisionRevision:
    id: UUID
    session_id: UUID
    actor_id: UUID
    case_version_id: UUID
    revision_no: int
    flow_step_code: str
    responses: dict[UUID, Any]
    private_reason_snapshot: dict[str, Any] | None
    exposure_sequence_at_commit: int
    contribution_class: ContributionClass
    commit_idempotency_key: str
    committed_at: datetime


@dataclass(frozen=True, slots=True)
class Exposure:
    id: UUID
    session_id: UUID
    actor_id: UUID
    case_version_id: UUID
    sequence_no: int
    flow_step_code: str
    resource_category: str
    resource_ref: str | None
    primitive_code: str
    capability_codes: tuple[str, ...]
    metadata: dict[str, Any]
    idempotency_key: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class Intervention:
    id: UUID
    session_id: UUID
    exposure_id: UUID | None
    type_code: str
    dimension_code: str | None
    metadata: dict[str, Any]
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class DecisionDelta:
    id: UUID
    session_id: UUID
    from_revision_id: UUID
    to_revision_id: UUID
    intervention_ids: tuple[UUID, ...]
    diff_snapshot: dict[str, Any]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RevisionCommitAttempt:
    status: RevisionCommitStatus
    revision: DecisionRevision | None
    delta: DecisionDelta | None = None
    missing_question_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class LineageSnapshot:
    session_id: UUID
    case_version_id: UUID
    revisions: tuple[DecisionRevision, ...]
    exposures: tuple[Exposure, ...]
    interventions: tuple[Intervention, ...]
    deltas: tuple[DecisionDelta, ...]
