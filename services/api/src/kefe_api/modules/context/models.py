from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ClaimStatus(StrEnum):
    VERIFIED = "VERIFIED"
    CLAIMED = "CLAIMED"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"


class DisclosureLevel(StrEnum):
    ESSENTIAL = "ESSENTIAL"
    DETAIL = "DETAIL"


class SourceKind(StrEnum):
    OFFICIAL = "OFFICIAL"
    NEWS = "NEWS"
    RESEARCH = "RESEARCH"
    EDITORIAL = "EDITORIAL"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class ContextSource:
    id: UUID
    case_version_id: UUID
    title: str
    publisher: str
    source_kind: SourceKind
    url: str | None = None
    published_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ContextBlock:
    id: UUID
    case_version_id: UUID
    display_order: int
    disclosure_level: DisclosureLevel
    title: str
    body: str
    claim_status: ClaimStatus
    source_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    case_version_id: UUID
    blocks: tuple[ContextBlock, ...]
    sources: tuple[ContextSource, ...]
