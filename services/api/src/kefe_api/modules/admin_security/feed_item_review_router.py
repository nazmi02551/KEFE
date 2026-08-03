from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from kefe_api.modules.admin_security.feed_item_review import (
    FeedItemReviewPage,
    FeedItemReviewRecord,
    SecuredFeedItemReviewService,
)
from kefe_api.modules.admin_security.proposal_queue import SecuredProposalQueueService
from kefe_api.modules.admin_security.router import ReadPrincipalDep, StrictModel
from kefe_api.modules.ingestion_orchestration.review_queue import (
    ProposalQueueReviewState,
)

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class FeedItemReviewSummaryResponse(StrictModel):
    proposal_id: UUID
    source_artifact_id: UUID
    feed_format: str
    feed_title: str
    item_id: str
    item_title: str
    item_url: str | None
    published_at: datetime | None
    created_at: datetime
    review_state: str
    risk_code: str
    locale: str | None
    jurisdiction_code: str | None


class FeedItemReviewPageResponse(StrictModel):
    items: list[FeedItemReviewSummaryResponse]
    next_cursor: str | None


class FeedItemReviewDecisionResponse(StrictModel):
    proposal_review_decision_id: UUID
    decision: str
    reviewer_ref: str
    decided_at: datetime
    rationale: str | None
    reason_code: str | None
    policy_version: str | None
    risk_policy_version: str | None


class FeedItemReviewDetailResponse(FeedItemReviewSummaryResponse):
    feed_content_hash: str
    evidence_ref: str
    summary_text: str | None
    run_id: UUID
    pipeline_code: str
    pipeline_version: str
    configuration_version: str
    review: FeedItemReviewDecisionResponse | None


def get_feed_item_review(request: Request) -> SecuredFeedItemReviewService:
    queue = SecuredProposalQueueService(
        repository=request.app.state.proposal_review_queue_repository,
        security=request.app.state.admin_security_service,
    )
    return SecuredFeedItemReviewService(
        queue=queue,
        knowledge=request.app.state.knowledge_repository,
    )


FeedItemReviewDep = Annotated[
    SecuredFeedItemReviewService,
    Depends(get_feed_item_review),
]


@router.get("/feed-items", response_model=FeedItemReviewPageResponse)
def list_feed_items(
    principal: ReadPrincipalDep,
    review: FeedItemReviewDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(min_length=1, max_length=1000)] = None,
    review_state: ProposalQueueReviewState | None = None,
    run_id: UUID | None = None,
) -> FeedItemReviewPageResponse:
    page: FeedItemReviewPage = review.list_feed_items(
        principal,
        limit=limit,
        cursor=cursor,
        review_state=review_state,
        run_id=run_id,
    )
    return FeedItemReviewPageResponse(
        items=[_summary(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.get(
    "/feed-items/{proposal_id}",
    response_model=FeedItemReviewDetailResponse,
)
def feed_item_detail(
    proposal_id: UUID,
    principal: ReadPrincipalDep,
    review: FeedItemReviewDep,
) -> FeedItemReviewDetailResponse:
    record = review.detail(principal, proposal_id)
    queue_record = record.queue_record
    proposal = queue_record.proposal
    run = queue_record.run
    decision = queue_record.review
    review_response = None
    if decision is not None:
        review_response = FeedItemReviewDecisionResponse(
            proposal_review_decision_id=decision.id,
            decision=decision.decision.value,
            reviewer_ref=decision.reviewer_ref,
            decided_at=decision.decided_at,
            rationale=decision.rationale,
            reason_code=decision.reason_code,
            policy_version=decision.policy_version,
            risk_policy_version=decision.risk_policy_version,
        )
    return FeedItemReviewDetailResponse(
        **_summary(record).model_dump(),
        feed_content_hash=record.payload.feed_content_hash,
        evidence_ref=record.payload.feed_storage_ref,
        summary_text=record.payload.summary_text,
        run_id=run.id,
        pipeline_code=run.pipeline_code,
        pipeline_version=run.pipeline_version,
        configuration_version=proposal.configuration_version or "",
        review=review_response,
    )


def _summary(record: FeedItemReviewRecord) -> FeedItemReviewSummaryResponse:
    queue_record = record.queue_record
    proposal = queue_record.proposal
    run = queue_record.run
    payload = record.payload
    return FeedItemReviewSummaryResponse(
        proposal_id=proposal.id,
        source_artifact_id=payload.source_artifact_id,
        feed_format=payload.feed_format,
        feed_title=payload.feed_title,
        item_id=payload.item_id,
        item_title=payload.item_title,
        item_url=payload.item_url,
        published_at=payload.published_at,
        created_at=proposal.created_at,
        review_state=queue_record.review_state.value,
        risk_code=proposal.risk_code or "",
        locale=run.locale,
        jurisdiction_code=run.jurisdiction_code,
    )


__all__ = ["router"]
