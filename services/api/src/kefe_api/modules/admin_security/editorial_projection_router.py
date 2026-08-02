from __future__ import annotations

from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from pydantic import Field, model_validator

from kefe_api.modules.admin_security.editorial_projection import (
    SecuredEditorialProjectionService,
)
from kefe_api.modules.admin_security.proposal_review import (
    SecuredProposalReviewService,
)
from kefe_api.modules.admin_security.router import StrictModel, WritePrincipalDep
from kefe_api.modules.ingestion_orchestration.models import (
    ProposalReviewDecisionKind,
)

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class ProposalReviewRequest(StrictModel):
    decision: ProposalReviewDecisionKind
    rationale: str | None = Field(default=None, max_length=5000)
    reason_code: str | None = Field(default=None, min_length=1, max_length=120)
    policy_version: str | None = Field(default=None, min_length=1, max_length=120)
    risk_policy_version: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )


class ProposalReviewResponse(StrictModel):
    proposal_review_decision_id: UUID
    proposal_id: UUID
    decision: str
    reviewer_ref: str
    decided_at: datetime
    rationale: str | None
    reason_code: str | None
    policy_version: str | None
    risk_policy_version: str | None


class EditorialProjectionRequest(StrictModel):
    proposal_review_decision_id: UUID
    profile_code: str = Field(min_length=1, max_length=120)
    profile_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=1, max_length=200)
    explicit_flow_template_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )
    explicit_flow_template_version: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_explicit_flow_pair(self) -> Self:
        if (self.explicit_flow_template_code is None) != (
            self.explicit_flow_template_version is None
        ):
            raise ValueError(
                "explicit Flow template code and version must be provided together"
            )
        return self


class EditorialProjectionResponse(StrictModel):
    projection_record_id: UUID
    candidate_proposal_id: UUID
    proposal_review_decision_id: UUID
    profile_code: str
    profile_version: int
    authoring_case_id: UUID
    authoring_case_version_id: UUID
    lifecycle_state: str
    replayed: bool
    created_at: datetime


def get_proposal_review(request: Request) -> SecuredProposalReviewService:
    return SecuredProposalReviewService(
        orchestration=request.app.state.ingestion_orchestration_service,
        security=request.app.state.admin_security_service,
    )


def get_projection(request: Request) -> SecuredEditorialProjectionService:
    return request.app.state.secured_editorial_projection_service


ProposalReviewDep = Annotated[
    SecuredProposalReviewService,
    Depends(get_proposal_review),
]
ProjectionDep = Annotated[
    SecuredEditorialProjectionService,
    Depends(get_projection),
]


@router.post(
    "/proposals/{proposal_id}/review",
    response_model=ProposalReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def review_proposal(
    proposal_id: UUID,
    body: ProposalReviewRequest,
    principal: WritePrincipalDep,
    review: ProposalReviewDep,
) -> ProposalReviewResponse:
    decision = review.review(
        principal,
        proposal_id=proposal_id,
        decision=body.decision,
        rationale=body.rationale,
        reason_code=body.reason_code,
        policy_version=body.policy_version,
        risk_policy_version=body.risk_policy_version,
    )
    return ProposalReviewResponse(
        proposal_review_decision_id=decision.id,
        proposal_id=decision.proposal_id,
        decision=decision.decision.value,
        reviewer_ref=decision.reviewer_ref,
        decided_at=decision.decided_at,
        rationale=decision.rationale,
        reason_code=decision.reason_code,
        policy_version=decision.policy_version,
        risk_policy_version=decision.risk_policy_version,
    )


@router.post(
    "/candidate-proposals/{candidate_proposal_id}/projection",
    response_model=EditorialProjectionResponse,
)
def project_candidate_case(
    candidate_proposal_id: UUID,
    body: EditorialProjectionRequest,
    principal: WritePrincipalDep,
    projection: ProjectionDep,
) -> EditorialProjectionResponse:
    result = projection.project(
        principal,
        candidate_proposal_id=candidate_proposal_id,
        proposal_review_decision_id=body.proposal_review_decision_id,
        profile_code=body.profile_code,
        profile_version=body.profile_version,
        idempotency_key=body.idempotency_key,
        explicit_flow_template_code=body.explicit_flow_template_code,
        explicit_flow_template_version=body.explicit_flow_template_version,
    )
    record = result.record
    return EditorialProjectionResponse(
        projection_record_id=record.id,
        candidate_proposal_id=record.candidate_proposal_id,
        proposal_review_decision_id=record.proposal_review_decision_id,
        profile_code=record.profile_code,
        profile_version=record.profile_version,
        authoring_case_id=record.authoring_case_id,
        authoring_case_version_id=record.authoring_case_version_id,
        lifecycle_state="DRAFT",
        replayed=result.replayed,
        created_at=record.created_at,
    )
