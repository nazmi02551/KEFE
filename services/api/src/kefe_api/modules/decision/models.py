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


class ClaimStatus(StrEnum):
    VERIFIED = "VERIFIED"
    CLAIMED = "CLAIMED"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"


class ClaimPresentation(StrEnum):
    CRITICAL = "CRITICAL"
    DETAIL = "DETAIL"


class ContextKind(StrEnum):
    CONTEXT = "CONTEXT"
    LEGAL_FRAME = "LEGAL_FRAME"
    CULTURAL_CONTEXT = "CULTURAL_CONTEXT"
    METHODOLOGY = "METHODOLOGY"


class ExposureKind(StrEnum):
    CLAIM = "CLAIM"
    CONTEXT_BLOCK = "CONTEXT_BLOCK"
    SOURCE = "SOURCE"


class DraftUpdateStatus(StrEnum):
    UPDATED = "UPDATED"
    NOT_FOUND = "NOT_FOUND"
    NOT_EDITABLE = "NOT_EDITABLE"


class CommitStatus(StrEnum):
    COMMITTED = "COMMITTED"
    IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY"
    NOT_FOUND = "NOT_FOUND"
    ALREADY_COMMITTED = "ALREADY_COMMITTED"
    STALE_VERSION = "STALE_VERSION"
    INCOMPLETE = "INCOMPLETE"
    IDEMPOTENCY_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"


@dataclass(frozen=True, slots=True)
class Source:
    id: UUID
    title: str
    publisher: str
    url: str
    published_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Claim:
    id: UUID
    text: str
    status: ClaimStatus
    presentation: ClaimPresentation
    source_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class ContextBlock:
    id: UUID
    kind: ContextKind
    title: str
    body: str


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
    critical_claims: tuple[Claim, ...] = ()
    detail_claims: tuple[Claim, ...] = ()
    context_blocks: tuple[ContextBlock, ...] = ()
    sources: tuple[Source, ...] = ()
    accepts_weighs: bool = True

    def exposure_ids(self, kind: ExposureKind) -> frozenset[UUID]:
        if kind is ExposureKind.CLAIM:
            return frozenset(claim.id for claim in (*self.critical_claims, *self.detail_claims))
        if kind is ExposureKind.CONTEXT_BLOCK:
            return frozenset(block.id for block in self.context_blocks)
        if kind is ExposureKind.SOURCE:
            return frozenset(source.id for source in self.sources)
        return frozenset()


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
class Exposure:
    kind: ExposureKind
    ref_id: UUID
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class DraftUpdateAttempt:
    status: DraftUpdateStatus
    session: WeighSession | None


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
