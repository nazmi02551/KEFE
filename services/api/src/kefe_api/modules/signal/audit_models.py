from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class SignalAuditEventType(StrEnum):
    THRESHOLD_CROSSED = "THRESHOLD_CROSSED"
    EDITORIAL_CERTIFIED = "EDITORIAL_CERTIFIED"
    METRIC_REFRESHED = "METRIC_REFRESHED"
    AUTHORITY_REVOKED = "AUTHORITY_REVOKED"


@dataclass(frozen=True, slots=True)
class SignalAuditEvent:
    audit_id: UUID
    signal_id: UUID
    case_version_id: UUID
    event_type: SignalAuditEventType
    actor_ref: str
    evidence_snapshot: dict[str, Any]
    occurred_at: datetime
    previous_hash: str | None
    entry_hash: str
