from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ActionStatus(StrEnum):
    PROPOSED = "PROPOSED"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFIED_COMPLETE = "VERIFIED_COMPLETE"
    STALLED = "STALLED"


@dataclass(frozen=True, slots=True)
class ActionMilestone:
    action_id: UUID
    case_version_id: UUID
    title: str
    description: str
    status: ActionStatus
    progress_percentage: int
    created_at: datetime
    institution_response_id: UUID | None = None
    target_completion_date: datetime | None = None
    evidence_summary: str | None = None
    evidence_url: str | None = None
