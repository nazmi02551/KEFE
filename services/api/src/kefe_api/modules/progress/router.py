from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from kefe_api.modules.identity.dependencies import PrincipalDep
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


class ProgressEnvelopeResponse(BaseModel):
    account_offer: AccountOfferResponse
    progress: ProgressResponse
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
    return ProgressEnvelopeResponse(
        account_offer=AccountOfferResponse(eligible=snapshot.account_offer_eligible),
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
        methodology={
            "sample_scope": "CURRENT_ACTOR_COMMITTED_HISTORY",
            "readiness_note": "PRESENTATION_ONLY_NOT_RESEARCH_VALIDATED",
            "advanced_insights": "DEFERRED",
        },
    )
