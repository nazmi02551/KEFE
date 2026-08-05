from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class MediaKind(StrEnum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class MediaState(StrEnum):
    REGISTERED = "REGISTERED"
    READY = "READY"
    RETIRED = "RETIRED"


class MediaSlot(StrEnum):
    HERO = "HERO"
    CONTEXT = "CONTEXT"
    REVEAL = "REVEAL"
    IMPACT = "IMPACT"


@dataclass(frozen=True, slots=True)
class MediaAsset:
    media_asset_id: UUID
    asset_key: str
    kind: MediaKind
    delivery_ref: str
    content_hash: str
    byte_length: int
    media_type: str
    title: str
    alt_text: str
    caption: str | None
    credit_label: str
    source_label: str
    poster_asset_key: str | None
    state: MediaState
    registered_by: str
    registered_at: datetime


@dataclass(frozen=True, slots=True)
class MediaBinding:
    binding_id: UUID
    case_version_id: UUID
    media_asset_id: UUID
    slot: MediaSlot
    priority: int
    autoplay: bool
    muted: bool
    looping: bool
    bound_by: str
    bound_at: datetime


@dataclass(frozen=True, slots=True)
class MediaAuditEntry:
    audit_id: UUID
    media_asset_id: UUID
    actor_ref: str
    command: str
    previous_state: MediaState | None
    new_state: MediaState
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class MediaAssetWriteResult:
    asset: MediaAsset
    replayed: bool


@dataclass(frozen=True, slots=True)
class MediaBindingWriteResult:
    binding: MediaBinding
    replayed: bool


@dataclass(frozen=True, slots=True)
class CaseMediaProjection:
    asset_key: str
    kind: MediaKind
    slot: MediaSlot
    delivery_ref: str
    title: str
    alt_text: str
    caption: str | None
    credit_label: str
    source_label: str
    poster_asset_key: str | None
    autoplay: bool
    muted: bool
    looping: bool
    priority: int
