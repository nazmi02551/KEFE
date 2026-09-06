from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MilestoneStatus(StrEnum):
    PROMISED = "PROMISED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED_VERIFIED = "DELIVERED_VERIFIED"
    DELAYED_OR_BROKEN = "DELAYED_OR_BROKEN"


@dataclass(frozen=True, slots=True)
class ImpactActionResult:
    action_id: str
    institution_name: str
    pledge_title: str
    milestone_status: MilestoneStatus
    completion_percentage: int
    target_completion_utc: str


class ImpactActionTracker:
    @staticmethod
    def evaluate(
        *,
        action_id: str,
        institution_name: str,
        pledge_title: str,
        milestone_status: MilestoneStatus,
        completion_percentage: int,
        target_completion_utc: str,
    ) -> ImpactActionResult:
        if not 0 <= completion_percentage <= 100:
            raise ValueError(f"completion_percentage must be in [0, 100], got {completion_percentage}")
        if len(institution_name.strip()) < 3:
            raise ValueError("institution_name must have at least 3 characters")
        if len(pledge_title.strip()) < 5:
            raise ValueError("pledge_title must have at least 5 characters")

        return ImpactActionResult(
            action_id=action_id.strip(),
            institution_name=institution_name.strip(),
            pledge_title=pledge_title.strip(),
            milestone_status=milestone_status,
            completion_percentage=completion_percentage,
            target_completion_utc=target_completion_utc.strip(),
        )
