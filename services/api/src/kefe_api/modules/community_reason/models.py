from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class CommunityReasonModeration(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"


class CommunityReasonModerationQueueKind(StrEnum):
    PENDING = "PENDING"
    REPORTED = "REPORTED"


class CommunityReasonModerationWriteStatus(StrEnum):
    APPLIED = "APPLIED"
    NOT_FOUND = "NOT_FOUND"
    CONFLICT = "CONFLICT"


class ReasonReaction(StrEnum):
    RESONATES = "RESONATES"
    USEFUL = "USEFUL"
    CHALLENGES = "CHALLENGES"


class ReasonReportCode(StrEnum):
    ABUSE = "ABUSE"
    PERSONAL_DATA = "PERSONAL_DATA"
    MISLEADING = "MISLEADING"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class CommunityReason:
    id: UUID
    actor_id: UUID
    session_id: UUID
    case_version_id: UUID
    tags: tuple[str, ...]
    body: str | None
    moderation_state: CommunityReasonModeration
    created_at: datetime
    updated_at: datetime

    @property
    def publicly_readable(self) -> bool:
        return self.moderation_state in {
            CommunityReasonModeration.NOT_REQUIRED,
            CommunityReasonModeration.ALLOWED,
        }


@dataclass(frozen=True, slots=True)
class PublicCommunityReason:
    id: UUID
    tags: tuple[str, ...]
    body: str | None
    reaction_counts: Mapping[str, int]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class CommunityReasonSnapshot:
    reasons: tuple[PublicCommunityReason, ...]
    tag_pattern_counts: Mapping[str, int]
    sample_size: int


@dataclass(frozen=True, slots=True)
class CommunityReasonModerationItem:
    reason_id: UUID
    case_version_id: UUID
    tags: tuple[str, ...]
    body: str | None
    moderation_state: CommunityReasonModeration
    created_at: datetime
    updated_at: datetime
    report_count: int
    report_counts_by_code: Mapping[str, int]
    latest_reported_at: datetime | None
    candidate_at: datetime


@dataclass(frozen=True, slots=True)
class CommunityReasonModerationAudit:
    audit_id: UUID
    reason_id: UUID
    actor_ref: str
    previous_state: CommunityReasonModeration
    decided_state: CommunityReasonModeration
    rationale: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class CommunityReasonModerationDecision:
    reason: CommunityReason
    audit: CommunityReasonModerationAudit


@dataclass(frozen=True, slots=True)
class CommunityReasonModerationWriteResult:
    status: CommunityReasonModerationWriteStatus
    decision: CommunityReasonModerationDecision | None = None
    current_state: CommunityReasonModeration | None = None
