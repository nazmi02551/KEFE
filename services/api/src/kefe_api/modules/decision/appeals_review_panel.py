from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AppealVerdict(StrEnum):
    OVERTURNED_RESTORED = "OVERTURNED_RESTORED"
    UPHELD_VIOLATION_CONFIRMED = "UPHELD_VIOLATION_CONFIRMED"
    PARTIAL_REVISION_PERMITTED = "PARTIAL_REVISION_PERMITTED"


@dataclass(frozen=True, slots=True)
class AppealsReviewResult:
    appeal_id: str
    target_resource_id: str
    appeal_verdict: AppealVerdict
    panelist_count: int
    favor_ratio: float
    resolution_summary: str


class AppealsReviewPanelService:
    @staticmethod
    def resolve_appeal(
        *,
        appeal_id: str,
        target_resource_id: str,
        panelist_count: int,
        votes_to_overturn: int,
        resolution_summary: str,
    ) -> AppealsReviewResult:
        if panelist_count < 3:
            raise ValueError("panelist_count must be at least 3")
        if not 0 <= votes_to_overturn <= panelist_count:
            raise ValueError(f"votes_to_overturn must be in [0, {panelist_count}]")
        if len(resolution_summary.strip()) < 10:
            raise ValueError("resolution_summary must have at least 10 characters")

        favor_ratio = votes_to_overturn / panelist_count

        if favor_ratio >= 0.67:
            verdict = AppealVerdict.OVERTURNED_RESTORED
        elif favor_ratio >= 0.40:
            verdict = AppealVerdict.PARTIAL_REVISION_PERMITTED
        else:
            verdict = AppealVerdict.UPHELD_VIOLATION_CONFIRMED

        return AppealsReviewResult(
            appeal_id=appeal_id.strip(),
            target_resource_id=target_resource_id.strip(),
            appeal_verdict=verdict,
            panelist_count=panelist_count,
            favor_ratio=round(favor_ratio, 2),
            resolution_summary=resolution_summary.strip(),
        )
