from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ShareRecord:
    id: UUID
    token_hash: str
    actor_id: UUID
    session_id: UUID
    case_id: UUID
    case_version_id: UUID
    include_decision: bool
    decision_snapshot: dict[str, Any] | None
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class PublicShare:
    share_id: UUID
    case_id: UUID
    case_version_id: UUID
    title: str
    summary: str
    primary_domain: str
    decision: dict[str, Any] | None
    created_at: datetime
    expires_at: datetime
