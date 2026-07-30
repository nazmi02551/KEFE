from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from kefe_api.modules.community_reason.models import ReasonReaction, ReasonReportCode
from kefe_api.modules.community_reason.service import CommunityReasonService
from kefe_api.modules.identity.dependencies import PrincipalDep

router = APIRouter(prefix="/v1", tags=["Community Reason"])


class PublishCommunityReasonRequest(BaseModel):
    tags: list[str] = Field(min_length=1, max_length=5)
    text: str | None = Field(default=None, max_length=300)


class CommunityReasonReceipt(BaseModel):
    reason_id: UUID
    tags: list[str]
    text: str | None
    moderation_state: str


class CommunityReasonItem(BaseModel):
    reason_id: UUID
    tags: list[str]
    text: str | None
    reaction_counts: dict[str, int]


class CommunityReasonSnapshotResponse(BaseModel):
    items: list[CommunityReasonItem]
    tag_pattern_counts: dict[str, int]
    sample_size: int
    methodology_note: str = (
        "Descriptive post-Commit Community Reasons; reactions do not rank truth or Signal eligibility."
    )


class ReactionRequest(BaseModel):
    reaction: ReasonReaction


class ReportRequest(BaseModel):
    code: ReasonReportCode


def get_service(request: Request) -> CommunityReasonService:
    return request.app.state.community_reason_service


CommunityReasonServiceDep = Annotated[CommunityReasonService, Depends(get_service)]


@router.post(
    "/weigh-sessions/{session_id}/community-reason",
    response_model=CommunityReasonReceipt,
)
def publish_reason(
    session_id: UUID,
    body: PublishCommunityReasonRequest,
    principal: PrincipalDep,
    service: CommunityReasonServiceDep,
) -> CommunityReasonReceipt:
    reason = service.publish(
        actor_id=principal.actor_id,
        session_id=session_id,
        tags=body.tags,
        body=body.text,
    )
    return CommunityReasonReceipt(
        reason_id=reason.id,
        tags=list(reason.tags),
        text=reason.body,
        moderation_state=reason.moderation_state.value,
    )


@router.get(
    "/case-versions/{case_version_id}/community-reasons",
    response_model=CommunityReasonSnapshotResponse,
)
def read_reasons(
    case_version_id: UUID,
    service: CommunityReasonServiceDep,
) -> CommunityReasonSnapshotResponse:
    snapshot = service.snapshot(case_version_id=case_version_id)
    return CommunityReasonSnapshotResponse(
        items=[
            CommunityReasonItem(
                reason_id=item.id,
                tags=list(item.tags),
                text=item.body,
                reaction_counts=dict(item.reaction_counts),
            )
            for item in snapshot.reasons
        ],
        tag_pattern_counts=dict(snapshot.tag_pattern_counts),
        sample_size=snapshot.sample_size,
    )


@router.put("/community-reasons/{reason_id}/reaction", status_code=204)
def react(
    reason_id: UUID,
    body: ReactionRequest,
    principal: PrincipalDep,
    service: CommunityReasonServiceDep,
) -> None:
    service.react(actor_id=principal.actor_id, reason_id=reason_id, reaction=body.reaction)


@router.post("/community-reasons/{reason_id}/reports", status_code=204)
def report(
    reason_id: UUID,
    body: ReportRequest,
    principal: PrincipalDep,
    service: CommunityReasonServiceDep,
) -> None:
    service.report(actor_id=principal.actor_id, reason_id=reason_id, report_code=body.code)
