from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ProgressReadiness(StrEnum):
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    FORMING = "FORMING"


@dataclass(frozen=True, slots=True)
class RecentCompletedCase:
    case_id: UUID
    case_version_id: UUID
    title: str
    primary_domain: str
    committed_at: datetime


@dataclass(frozen=True, slots=True)
class ProgressSnapshot:
    actor_id: UUID
    meaningful_weigh_count: int
    distinct_case_count: int
    distinct_domain_count: int
    first_committed_at: datetime | None
    last_committed_at: datetime | None
    recent_cases: tuple[RecentCompletedCase, ...]

    @property
    def readiness(self) -> ProgressReadiness:
        if self.meaningful_weigh_count < 3:
            return ProgressReadiness.INSUFFICIENT_DATA
        return ProgressReadiness.FORMING

    @property
    def account_offer_eligible(self) -> bool:
        return self.meaningful_weigh_count >= 1
