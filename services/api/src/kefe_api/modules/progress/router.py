from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from kefe_api.modules.identity.dependencies import PrincipalDep
from kefe_api.modules.identity.models import ActorKind
from kefe_api.modules.progress.service import ProgressService

router = APIRouter(prefix="/v1/me", tags=["Progress"])


class AccountOfferResponse(BaseModel):
    eligible: bool
    placement: str = "POST_REVEAL"
    blocking: bool = False
    dismissible: bool = True
    continue_as_guest_available: bool = True
    account_creation_available: bool = False


class RecentCaseResponse(BaseModel):
    case_id: str
    case_version_id: str
    title: str
    primary_domain: str
    committed_at: str


class ProgressResponse(BaseModel):
    readiness: str
    meaningful_weigh_count: int
    distinct_case_count: int
    distinct_domain_count: int
    first_committed_at: str | None
    last_committed_at: str | None
    recent_cases: list[RecentCaseResponse]


class DomainActivityResponse(BaseModel):
    primary_domain: str
    committed_weigh_count: int
    last_committed_at: str


class RecentJourneyResponse(BaseModel):
    case_id: str
    case_version_id: str
    title: str
    primary_domain: str
    initial_committed_at: str
    latest_decision_at: str
    decision_update_count: int
    reflection_completed: bool


class JourneyResponse(BaseModel):
    decision_update_count: int
    revisited_case_count: int
    reflection_completion_count: int
    domain_activity: list[DomainActivityResponse]
    recent_journeys: list[RecentJourneyResponse]


class ProgressEnvelopeResponse(BaseModel):
    account_offer: AccountOfferResponse
    progress: ProgressResponse
    journey: JourneyResponse
    methodology: dict[str, str]


def get_progress_service(request: Request) -> ProgressService:
    return request.app.state.progress_service


ProgressServiceDep = Annotated[ProgressService, Depends(get_progress_service)]


@router.get("/progress", response_model=ProgressEnvelopeResponse)
def get_progress(
    principal: PrincipalDep,
    service: ProgressServiceDep,
) -> ProgressEnvelopeResponse:
    snapshot = service.get_progress(principal.actor_id)
    journey = service.get_journey(principal.actor_id)
    guest = principal.actor_kind is ActorKind.GUEST
    return ProgressEnvelopeResponse(
        account_offer=AccountOfferResponse(
            eligible=snapshot.account_offer_eligible and guest,
            account_creation_available=guest,
        ),
        progress=ProgressResponse(
            readiness=snapshot.readiness.value,
            meaningful_weigh_count=snapshot.meaningful_weigh_count,
            distinct_case_count=snapshot.distinct_case_count,
            distinct_domain_count=snapshot.distinct_domain_count,
            first_committed_at=(
                snapshot.first_committed_at.isoformat() if snapshot.first_committed_at else None
            ),
            last_committed_at=(
                snapshot.last_committed_at.isoformat() if snapshot.last_committed_at else None
            ),
            recent_cases=[
                RecentCaseResponse(
                    case_id=str(item.case_id),
                    case_version_id=str(item.case_version_id),
                    title=item.title,
                    primary_domain=item.primary_domain,
                    committed_at=item.committed_at.isoformat(),
                )
                for item in snapshot.recent_cases
            ],
        ),
        journey=JourneyResponse(
            decision_update_count=journey.decision_update_count,
            revisited_case_count=journey.revisited_case_count,
            reflection_completion_count=journey.reflection_completion_count,
            domain_activity=[
                DomainActivityResponse(
                    primary_domain=item.primary_domain,
                    committed_weigh_count=item.committed_weigh_count,
                    last_committed_at=item.last_committed_at.isoformat(),
                )
                for item in journey.domain_activity
            ],
            recent_journeys=[
                RecentJourneyResponse(
                    case_id=str(item.case_id),
                    case_version_id=str(item.case_version_id),
                    title=item.title,
                    primary_domain=item.primary_domain,
                    initial_committed_at=item.initial_committed_at.isoformat(),
                    latest_decision_at=item.latest_decision_at.isoformat(),
                    decision_update_count=item.decision_update_count,
                    reflection_completed=item.reflection_completed,
                )
                for item in journey.recent_journeys
            ],
        ),
        methodology={
            "sample_scope": "CURRENT_ACTOR_COMMITTED_HISTORY",
            "readiness_note": "PRESENTATION_ONLY_NOT_RESEARCH_VALIDATED",
            "journey_semantics": "OBSERVED_PRODUCT_HISTORY_ONLY",
            "causal_claims": "NONE",
            "advanced_insights": "DEFERRED",
        },
    )
