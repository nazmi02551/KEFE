from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import Field

from kefe_api.modules.admin_security.proposal_review import (
    SecuredProposalReviewService,
)
from kefe_api.modules.admin_security.router import (
    ReadPrincipalDep,
    StrictModel,
    WritePrincipalDep,
)
from kefe_api.modules.ingestion_orchestration.models import (
    Proposal,
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
)

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class ProposalReviewDecisionResponse(StrictModel):
    review_decision_id: UUID
    proposal_id: UUID
    decision: ProposalReviewDecisionKind
    reviewer_ref: str
    decided_at: datetime
    rationale: str | None
    reason_code: str | None
    policy_version: str | None
    risk_policy_version: str | None


class ProposalReviewItemResponse(StrictModel):
    proposal_id: UUID
    proposal_kind: str
    payload_schema_ref: str
    payload_schema_version: str
    payload: dict[str, Any]
    payload_hash: str
    run_id: UUID
    stage_execution_id: UUID
    taxonomy_version: str | None
    configuration_version: str | None
    methodology_version: str | None
    confidence: float | None
    risk_code: str | None
    ai_execution_ref: str | None
    provenance_ref: str | None
    supersedes_proposal_id: UUID | None
    created_at: datetime
    review: ProposalReviewDecisionResponse | None = None


class ProposalReviewQueueResponse(StrictModel):
    items: list[ProposalReviewItemResponse]
    count: int


class ProposalReviewRequest(StrictModel):
    decision: ProposalReviewDecisionKind
    rationale: str | None = Field(default=None, max_length=4000)
    reason_code: str | None = Field(default=None, max_length=120)
    policy_version: str | None = Field(default=None, max_length=120)
    risk_policy_version: str | None = Field(default=None, max_length=120)


def get_proposal_review_service(request: Request) -> SecuredProposalReviewService:
    return request.app.state.secured_proposal_review_service


ProposalReviewServiceDep = Annotated[
    SecuredProposalReviewService,
    Depends(get_proposal_review_service),
]


def _review_response(
    review: ProposalReviewDecision,
) -> ProposalReviewDecisionResponse:
    return ProposalReviewDecisionResponse(
        review_decision_id=review.id,
        proposal_id=review.proposal_id,
        decision=review.decision,
        reviewer_ref=review.reviewer_ref,
        decided_at=review.decided_at,
        rationale=review.rationale,
        reason_code=review.reason_code,
        policy_version=review.policy_version,
        risk_policy_version=review.risk_policy_version,
    )


def _proposal_response(
    proposal: Proposal,
    review: ProposalReviewDecision | None = None,
) -> ProposalReviewItemResponse:
    return ProposalReviewItemResponse(
        proposal_id=proposal.id,
        proposal_kind=proposal.proposal_kind,
        payload_schema_ref=proposal.payload_schema_ref,
        payload_schema_version=proposal.payload_schema_version,
        payload=proposal.payload,
        payload_hash=proposal.payload_hash,
        run_id=proposal.run_id,
        stage_execution_id=proposal.stage_execution_id,
        taxonomy_version=proposal.taxonomy_version,
        configuration_version=proposal.configuration_version,
        methodology_version=proposal.methodology_version,
        confidence=proposal.confidence,
        risk_code=proposal.risk_code,
        ai_execution_ref=proposal.ai_execution_ref,
        provenance_ref=proposal.provenance_ref,
        supersedes_proposal_id=proposal.supersedes_proposal_id,
        created_at=proposal.created_at,
        review=_review_response(review) if review is not None else None,
    )


@router.get(
    "/proposals/review-queue",
    response_model=ProposalReviewQueueResponse,
)
def list_proposal_review_queue(
    principal: ReadPrincipalDep,
    service: ProposalReviewServiceDep,
    proposal_kind: str | None = Query(default=None, min_length=1, max_length=120),
    limit: int = Query(default=50, ge=1, le=100),
) -> ProposalReviewQueueResponse:
    proposals = service.list_pending(
        principal,
        proposal_kind=proposal_kind,
        limit=limit,
    )
    items = [_proposal_response(proposal) for proposal in proposals]
    return ProposalReviewQueueResponse(items=items, count=len(items))


@router.get(
    "/proposals/{proposal_id}",
    response_model=ProposalReviewItemResponse,
)
def get_proposal_review_detail(
    proposal_id: UUID,
    principal: ReadPrincipalDep,
    service: ProposalReviewServiceDep,
) -> ProposalReviewItemResponse:
    proposal, review = service.get(principal, proposal_id)
    return _proposal_response(proposal, review)


@router.post(
    "/proposals/{proposal_id}/review",
    response_model=ProposalReviewDecisionResponse,
)
def review_proposal(
    proposal_id: UUID,
    body: ProposalReviewRequest,
    principal: WritePrincipalDep,
    service: ProposalReviewServiceDep,
) -> ProposalReviewDecisionResponse:
    review = service.review(
        principal,
        proposal_id=proposal_id,
        decision=body.decision,
        rationale=body.rationale,
        reason_code=body.reason_code,
        policy_version=body.policy_version,
        risk_policy_version=body.risk_policy_version,
    )
    return _review_response(review)
