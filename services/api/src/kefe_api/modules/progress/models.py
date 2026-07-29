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


@dataclass(frozen=True, slots=True)
class DomainActivity:
    primary_domain: str
    committed_weigh_count: int
    last_committed_at: datetime


@dataclass(frozen=True, slots=True)
class RecentDecisionJourney:
    case_id: UUID
    case_version_id: UUID
    title: str
    primary_domain: str
    initial_committed_at: datetime
    latest_decision_at: datetime
    decision_update_count: int
    reflection_completed: bool


@dataclass(frozen=True, slots=True)
class DecisionJourneySnapshot:
    actor_id: UUID
    decision_update_count: int
    revisited_case_count: int
    reflection_completion_count: int
    domain_activity: tuple[DomainActivity, ...]
    recent_journeys: tuple[RecentDecisionJourney, ...]

    @classmethod
    def empty(cls, actor_id: UUID) -> DecisionJourneySnapshot:
        return cls(
            actor_id=actor_id,
            decision_update_count=0,
            revisited_case_count=0,
            reflection_completion_count=0,
            domain_activity=(),
            recent_journeys=(),
        )
