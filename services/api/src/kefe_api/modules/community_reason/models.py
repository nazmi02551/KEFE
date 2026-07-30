from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Mapping
from uuid import UUID


class CommunityReasonModeration(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING = "PENDING"
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"


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
