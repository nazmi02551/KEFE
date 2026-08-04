from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from kefe_api.modules.admin_security.feed_item_review import (
    FeedItemReviewRecord,
    SecuredFeedItemReviewService,
)
from kefe_api.modules.admin_security.proposal_queue import SecuredProposalQueueService
from kefe_api.modules.admin_security.router import ReadPrincipalDep, StrictModel
from kefe_api.modules.ingestion_orchestration.review_queue import ProposalQueueReviewState

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class FeedItemSummary(StrictModel):
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


class FeedItemPage(StrictModel):
    items: list[FeedItemSummary]
    next_cursor: str | None


class FeedItemDetail(FeedItemSummary):
    feed_content_hash: str
    evidence_ref: str
    summary_text: str | None
    run_id: UUID
    pipeline_code: str
    pipeline_version: str
    configuration_version: str


def get_service(request: Request) -> SecuredFeedItemReviewService:
    return SecuredFeedItemReviewService(
        queue=SecuredProposalQueueService(
            repository=request.app.state.proposal_review_queue_repository,
            security=request.app.state.admin_security_service,
        ),
        knowledge=request.app.state.knowledge_repository,
    )


ServiceDep = Annotated[SecuredFeedItemReviewService, Depends(get_service)]


@router.get("/feed-items", response_model=FeedItemPage)
def list_feed_items(
    principal: ReadPrincipalDep,
    service: ServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(min_length=1, max_length=1000)] = None,
    review_state: ProposalQueueReviewState | None = None,
    run_id: UUID | None = None,
) -> FeedItemPage:
    page = service.list_feed_items(
        principal,
        limit=limit,
        cursor=cursor,
        review_state=review_state,
        run_id=run_id,
    )
    return FeedItemPage(
        items=[_summary(record) for record in page.items],
        next_cursor=page.next_cursor,
    )


@router.get("/feed-items/{proposal_id}", response_model=FeedItemDetail)
def feed_item_detail(
    proposal_id: UUID,
    principal: ReadPrincipalDep,
    service: ServiceDep,
) -> FeedItemDetail:
    record = service.detail(principal, proposal_id)
    proposal = record.queue_record.proposal
    run = record.queue_record.run
    assert proposal.configuration_version is not None
    return FeedItemDetail(
        **_summary(record).model_dump(),
        feed_content_hash=record.payload.feed_content_hash,
        evidence_ref=record.payload.feed_storage_ref,
        summary_text=record.payload.summary_text,
        run_id=run.id,
        pipeline_code=run.pipeline_code,
        pipeline_version=run.pipeline_version,
        configuration_version=proposal.configuration_version,
    )


def _summary(record: FeedItemReviewRecord) -> FeedItemSummary:
    proposal = record.queue_record.proposal
    run = record.queue_record.run
    payload = record.payload
    assert proposal.risk_code is not None
    return FeedItemSummary(
        proposal_id=proposal.id,
        source_artifact_id=payload.source_artifact_id,
        feed_format=payload.feed_format,
        feed_title=payload.feed_title,
        item_id=payload.item_id,
        item_title=payload.item_title,
        item_url=payload.item_url,
        published_at=payload.published_at,
        created_at=proposal.created_at,
        review_state=record.queue_record.review_state.value,
        risk_code=proposal.risk_code,
        locale=run.locale,
        jurisdiction_code=run.jurisdiction_code,
    )


__all__ = ["router"]
