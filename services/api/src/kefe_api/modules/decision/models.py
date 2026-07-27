from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class WeighState(StrEnum):
    DRAFT = "DRAFT"
    COMMITTED = "COMMITTED"
    BLOCKED_BY_VERSION = "BLOCKED_BY_VERSION"


class DraftUpdateStatus(StrEnum):
    UPDATED = "UPDATED"
    NOT_FOUND = "NOT_FOUND"
    NOT_EDITABLE = "NOT_EDITABLE"


class ReasonModerationState(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"


class ReasonVisibility(StrEnum):
    PRIVATE = "PRIVATE"


class PerspectiveMode(StrEnum):
    READY = "READY"
    CLUSTER_PENDING = "CLUSTER_PENDING"
    DEGRADED_CURATED = "DEGRADED_CURATED"


class PerspectiveSlot(StrEnum):
    NEAR = "NEAR"
    OPPOSING = "OPPOSING"
    BRIDGE = "BRIDGE"
    ALTERNATIVE_CONTEXT = "ALTERNATIVE_CONTEXT"


class PerspectiveSourceKind(StrEnum):
    CURATED = "CURATED"
    HUMAN_REASON = "HUMAN_REASON"


class CommitStatus(StrEnum):
    COMMITTED = "COMMITTED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    NOT_FOUND = "NOT_FOUND"
    ALREADY_COMMITTED = "ALREADY_COMMITTED"
    STALE_VERSION = "STALE_VERSION"
    INCOMPLETE = "INCOMPLETE"
    IDEMPOTENCY_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"


@dataclass(frozen=True, slots=True)
class Question:
    id: UUID
    prompt: str
    response_type: str
    required: bool = True
    response_schema: Mapping[str, Any] = field(default_factory=dict)

    @property
    def options(self) -> tuple[str, ...]:
        raw_options = self.response_schema.get("options", ())
        return tuple(str(option) for option in raw_options)


@dataclass(frozen=True, slots=True)
class CaseVersion:
    id: UUID
    case_id: UUID
    title: str
    summary: str
    base_format: str
    primary_domain: str
    content_risk: str
    version_no: int
    questions: tuple[Question, ...]
    accepts_weighs: bool = True


@dataclass(slots=True)
class WeighSession:
    id: UUID
    actor_id: UUID
    case_id: UUID
    case_version_id: UUID
    state: WeighState = WeighState.DRAFT
    responses: dict[UUID, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    committed_at: datetime | None = None
    commit_key: str | None = None


@dataclass(frozen=True, slots=True)
class PrivateReason:
    session_id: UUID
    tags: tuple[str, ...]
    text: str | None
    moderation_state: ReasonModerationState
    visibility: ReasonVisibility = ReasonVisibility.PRIVATE
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class PerspectiveCard:
    perspective_id: UUID
    slot: PerspectiveSlot
    body: str
    source_kind: PerspectiveSourceKind
    provenance_label: str
    moderation_state: ReasonModerationState


@dataclass(frozen=True, slots=True)
class PerspectiveSnapshot:
    case_version_id: UUID
    mode: PerspectiveMode
    sample_kind: str
    sample_size: int
    generated_at: datetime
    provenance_note: str
    cards: tuple[PerspectiveCard, ...]


@dataclass(frozen=True, slots=True)
class DraftUpdateAttempt:
    status: DraftUpdateStatus
    session: WeighSession | None


@dataclass(frozen=True, slots=True)
class ReasonUpdateAttempt:
    status: DraftUpdateStatus
    reason: PrivateReason | None


@dataclass(frozen=True, slots=True)
class CommitAttempt:
    status: CommitStatus
    session: WeighSession | None
    missing_question_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class RevealSnapshot:
    case_version_id: UUID
    layer: str
    n: int
    confidence: str
    generated_at: datetime
    payload: dict[str, Any]
