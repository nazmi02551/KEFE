from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ReflectionCompletion:
    id: UUID
    session_id: UUID
    actor_id: UUID
    case_version_id: UUID
    flow_step_code: str
    latest_revision_id: UUID
    latest_delta_id: UUID | None
    idempotency_key: str
    completed_at: datetime


class ReflectionCompletionStatus(StrEnum):
    COMPLETED = "COMPLETED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    ALREADY_COMPLETED = "ALREADY_COMPLETED"
    IDEMPOTENCY_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"


@dataclass(frozen=True, slots=True)
class ReflectionCompletionAttempt:
    status: ReflectionCompletionStatus
    completion: ReflectionCompletion | None


@dataclass(frozen=True, slots=True)
class ReflectionReadModel:
    session_id: UUID
    case_version_id: UUID
    flow_step_code: str
    revision_count: int
    latest_revision_id: UUID
    latest_delta_id: UUID | None
    decision_changed: bool
    changed_question_count: int
    intervention_count: int
    intervention_type_codes: tuple[str, ...]
    from_contribution_class: str | None
    to_contribution_class: str
    completed: bool
