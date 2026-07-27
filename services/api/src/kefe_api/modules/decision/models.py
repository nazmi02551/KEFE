from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class WeighState(StrEnum):
    DRAFT = "DRAFT"
    COMMITTED = "COMMITTED"
    BLOCKED_BY_VERSION = "BLOCKED_BY_VERSION"


@dataclass(frozen=True, slots=True)
class Question:
    id: UUID
    prompt: str
    response_type: str
    options: tuple[str, ...] = ()


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
class RevealSnapshot:
    case_version_id: UUID
    layer: str
    n: int
    confidence: str
    generated_at: datetime
    payload: dict[str, Any]
