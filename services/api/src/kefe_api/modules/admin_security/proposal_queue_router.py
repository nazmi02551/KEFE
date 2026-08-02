from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from kefe_api.modules.admin_security.proposal_queue import (
    SecuredProposalQueueService,
)
from kefe_api.modules.admin_security.router import ReadPrincipalDep, StrictModel
from kefe_api.modules.ingestion_orchestration.review_queue import (
    ProposalQueueRecord,
    ProposalQueueReviewState,
)

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class ProposalReviewSummaryResponse(StrictModel):
    proposal_review_decision_id: UUID
    decision: str
    reviewer_ref: str
    decided_at: datetime
    rationale: str | None
    reason_code: str | None
    policy_version: str | None
    risk_policy_version: str | None


class ProposalQueueItemResponse(StrictModel):
    proposal_id: UUID
    proposal_kind: str
    payload_schema_ref: str
    payload_schema_version: str
    payload_hash: str
    run_id: UUID
    stage_execution_id: UUID
    input_artifact_kind: str
    input_artifact_id: UUID
    pipeline_code: str
    pipeline_version: str
    locale: str | None
    jurisdiction_code: str | None
    proposal_taxonomy_version: str | None
    proposal_configuration_version: str | None
    proposal_methodology_version: str | None
    run_taxonomy_version: str | None
    run_methodology_version: str | None
    confidence: float | None
    risk_code: str | None
    ai_execution_ref: str | None
    provenance_ref: str | None
    supersedes_proposal_id: UUID | None
    created_at: datetime
    review_state: str
    review: ProposalReviewSummaryResponse | None


class ProposalQueueResponse(StrictModel):
    items: list[ProposalQueueItemResponse]
    next_cursor: str | None


class ProposalDetailResponse(ProposalQueueItemResponse):
    payload: dict[str, Any]


def get_proposal_queue(request: Request) -> SecuredProposalQueueService:
    return SecuredProposalQueueService(
        repository=request.app.state.proposal_review_queue_repository,
        security=request.app.state.admin_security_service,
    )


ProposalQueueDep = Annotated[
    SecuredProposalQueueService,
    Depends(get_proposal_queue),
]


@router.get("/proposals", response_model=ProposalQueueResponse)
def list_proposals(
    principal: ReadPrincipalDep,
    queue: ProposalQueueDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(min_length=1, max_length=1000)] = None,
    review_state: ProposalQueueReviewState | None = None,
    proposal_kind: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    risk_code: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    run_id: UUID | None = None,
    pipeline_code: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
) -> ProposalQueueResponse:
    page = queue.list_queue(
        principal,
        limit=limit,
        cursor=cursor,
        review_state=review_state,
        proposal_kind=proposal_kind,
        risk_code=risk_code,
        run_id=run_id,
        pipeline_code=pipeline_code,
    )
    return ProposalQueueResponse(
        items=[_item_response(record) for record in page.items],
        next_cursor=page.next_cursor,
    )


@router.get("/proposals/{proposal_id}", response_model=ProposalDetailResponse)
def proposal_detail(
    proposal_id: UUID,
    principal: ReadPrincipalDep,
    queue: ProposalQueueDep,
) -> ProposalDetailResponse:
    record = queue.detail(principal, proposal_id)
    return ProposalDetailResponse(
        **_item_response(record).model_dump(),
        payload=record.proposal.payload,
    )


def _item_response(record: ProposalQueueRecord) -> ProposalQueueItemResponse:
    proposal = record.proposal
    run = record.run
    review = record.review
    review_response = None
    if review is not None:
        review_response = ProposalReviewSummaryResponse(
            proposal_review_decision_id=review.id,
            decision=review.decision.value,
            reviewer_ref=review.reviewer_ref,
            decided_at=review.decided_at,
            rationale=review.rationale,
            reason_code=review.reason_code,
            policy_version=review.policy_version,
            risk_policy_version=review.risk_policy_version,
        )
    return ProposalQueueItemResponse(
        proposal_id=proposal.id,
        proposal_kind=proposal.proposal_kind,
        payload_schema_ref=proposal.payload_schema_ref,
        payload_schema_version=proposal.payload_schema_version,
        payload_hash=proposal.payload_hash,
        run_id=proposal.run_id,
        stage_execution_id=proposal.stage_execution_id,
        input_artifact_kind=run.input_artifact_kind.value,
        input_artifact_id=run.input_artifact_id,
        pipeline_code=run.pipeline_code,
        pipeline_version=run.pipeline_version,
        locale=run.locale,
        jurisdiction_code=run.jurisdiction_code,
        proposal_taxonomy_version=proposal.taxonomy_version,
        proposal_configuration_version=proposal.configuration_version,
        proposal_methodology_version=proposal.methodology_version,
        run_taxonomy_version=run.taxonomy_version,
        run_methodology_version=run.methodology_version,
        confidence=proposal.confidence,
        risk_code=proposal.risk_code,
        ai_execution_ref=proposal.ai_execution_ref,
        provenance_ref=proposal.provenance_ref,
        supersedes_proposal_id=proposal.supersedes_proposal_id,
        created_at=proposal.created_at,
        review_state=record.review_state.value,
        review=review_response,
    )
