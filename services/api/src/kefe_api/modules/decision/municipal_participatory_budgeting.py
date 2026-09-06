from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MunicipalProjectDomain(StrEnum):
    PARKS_AND_GREEN_SPACES = "PARKS_AND_GREEN_SPACES"
    PUBLIC_TRANSIT_AND_MOBILITY = "PUBLIC_TRANSIT_AND_MOBILITY"
    EDUCATION_AND_YOUTH_CENTERS = "EDUCATION_AND_YOUTH_CENTERS"
    DISASTER_RESILIENCE_AND_SAFETY = "DISASTER_RESILIENCE_AND_SAFETY"


@dataclass(frozen=True, slots=True)
class MunicipalBudgetProjectResult:
    project_id: str
    municipality_name: str
    project_domain: MunicipalProjectDomain
    requested_budget_try: int
    citizen_votes_count: int
    civic_approval_rate: float


class MunicipalParticipatoryBudgetingService:
    @staticmethod
    def submit_project(
        *,
        project_id: str,
        municipality_name: str,
        project_domain: MunicipalProjectDomain,
        requested_budget_try: int,
        citizen_votes_count: int,
        total_eligible_voters: int,
    ) -> MunicipalBudgetProjectResult:
        if len(municipality_name.strip()) < 3:
            raise ValueError("municipality_name must have at least 3 characters")
        if requested_budget_try < 1000:
            raise ValueError(f"requested_budget_try must be >= 1000, got {requested_budget_try}")
        if citizen_votes_count < 0:
            raise ValueError("citizen_votes_count cannot be negative")
        if total_eligible_voters <= 0:
            raise ValueError("total_eligible_voters must be > 0")

        approval_rate = min(1.0, citizen_votes_count / total_eligible_voters)

        return MunicipalBudgetProjectResult(
            project_id=project_id.strip(),
            municipality_name=municipality_name.strip(),
            project_domain=project_domain,
            requested_budget_try=requested_budget_try,
            citizen_votes_count=citizen_votes_count,
            civic_approval_rate=round(approval_rate, 2),
        )
