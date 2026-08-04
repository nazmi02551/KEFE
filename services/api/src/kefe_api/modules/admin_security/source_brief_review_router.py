from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from kefe_api.modules.admin_security.feed_item_review_router import get_service
from kefe_api.modules.admin_security.proposal_queue import SecuredProposalQueueService
from kefe_api.modules.admin_security.router import ReadPrincipalDep, StrictModel
from kefe_api.modules.admin_security.source_brief_review import (
    SecuredSourceBriefReviewService,
    SourceBriefReviewRecord,
)
from kefe_api.modules.ingestion_orchestration.review_queue import ProposalQueueReviewState

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class SourceBriefSummary(StrictModel):
    proposal_id: UUID
    normalized_artifact_id: UUID
    source_artifact_id: UUID
    headline: str
    source_url: str | None
    publisher_or_issuer: str | None
    published_at: datetime | None
    created_at: datetime
    review_state: str
    risk_code: str
    locale: str | None
    jurisdiction_code: str | None


class SourceBriefPage(StrictModel):
    items: list[SourceBriefSummary]
    next_cursor: str | None


class SourceBriefReviewDecision(StrictModel):
    proposal_review_decision_id: UUID
    decision: str
    reviewer_ref: str
    decided_at: datetime
    rationale: str | None
    reason_code: str | None
    policy_version: str | None
    risk_policy_version: str | None


class SourceBriefDetail(SourceBriefSummary):
    parent_feed_item_proposal_id: UUID
    parent_feed_item_review_decision_id: UUID
    source_content_hash: str
    evidence_ref: str
    feed_format: str
    source_feed_title: str
    source_item_id: str
    synopsis: str | None
    language_code: str | None
    run_id: UUID
    pipeline_code: str
    pipeline_version: str
    configuration_version: str
    review: SourceBriefReviewDecision | None


def get_source_brief_review(request: Request) -> SecuredSourceBriefReviewService:
    return SecuredSourceBriefReviewService(
        queue=SecuredProposalQueueService(
            repository=request.app.state.proposal_review_queue_repository,
            security=request.app.state.admin_security_service,
        ),
        feed_items=get_service(request),
        knowledge=request.app.state.knowledge_repository,
    )


ServiceDep = Annotated[
    SecuredSourceBriefReviewService,
    Depends(get_source_brief_review),
]


@router.get("/source-briefs", response_model=SourceBriefPage)
def list_source_briefs(
    principal: ReadPrincipalDep,
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(min_length=1, max_length=1000)] = None,
    review_state: ProposalQueueReviewState | None = None,
    run_id: UUID | None = None,
) -> SourceBriefPage:
    page = service.list_source_briefs(
        principal,
        limit=limit,
        cursor=cursor,
        review_state=review_state,
        run_id=run_id,
    )
    return SourceBriefPage(
        items=[_summary(record) for record in page.items],
        next_cursor=page.next_cursor,
    )


@router.get("/source-briefs/{proposal_id}", response_model=SourceBriefDetail)
def source_brief_detail(
    proposal_id: UUID,
    principal: ReadPrincipalDep,
    service: ServiceDep,
) -> SourceBriefDetail:
    record = service.detail(principal, proposal_id)
    proposal = record.queue_record.proposal
    run = record.queue_record.run
    decision = record.queue_record.review
    assert proposal.configuration_version is not None
    review_response = None
    if decision is not None:
        review_response = SourceBriefReviewDecision(
            proposal_review_decision_id=decision.id,
            decision=decision.decision.value,
            reviewer_ref=decision.reviewer_ref,
            decided_at=decision.decided_at,
            rationale=decision.rationale,
            reason_code=decision.reason_code,
            policy_version=decision.policy_version,
            risk_policy_version=decision.risk_policy_version,
        )
    return SourceBriefDetail(
        **_summary(record).model_dump(),
        parent_feed_item_proposal_id=record.payload.parent_feed_item_proposal_id,
        parent_feed_item_review_decision_id=record.payload.review_decision_id,
        source_content_hash=record.payload.source_content_hash,
        evidence_ref=record.payload.evidence_ref,
        feed_format=record.payload.feed_format,
        source_feed_title=record.normalized_metadata.feed_title,
        source_item_id=record.normalized_metadata.item_id,
        synopsis=record.payload.synopsis,
        language_code=record.payload.language_code,
        run_id=run.id,
        pipeline_code=run.pipeline_code,
        pipeline_version=run.pipeline_version,
        configuration_version=proposal.configuration_version,
        review=review_response,
    )


def _summary(record: SourceBriefReviewRecord) -> SourceBriefSummary:
    proposal = record.queue_record.proposal
    run = record.queue_record.run
    payload = record.payload
    assert proposal.risk_code is not None
    return SourceBriefSummary(
        proposal_id=proposal.id,
        normalized_artifact_id=payload.normalized_artifact_id,
        source_artifact_id=payload.source_artifact_id,
        headline=payload.headline,
        source_url=payload.source_url,
        publisher_or_issuer=payload.publisher_or_issuer,
        published_at=payload.published_at,
        created_at=proposal.created_at,
        review_state=record.queue_record.review_state.value,
        risk_code=proposal.risk_code,
        locale=run.locale,
        jurisdiction_code=run.jurisdiction_code,
    )


__all__ = ["router"]
