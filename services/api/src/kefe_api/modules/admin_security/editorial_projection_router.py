from __future__ import annotations

from datetime import datetime
from typing import Annotated, Self
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import Field, model_validator

from kefe_api.modules.admin_security.editorial_projection import (
    SecuredEditorialProjectionService,
)
from kefe_api.modules.admin_security.router import StrictModel, WritePrincipalDep

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


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


def get_projection(request: Request) -> SecuredEditorialProjectionService:
    return request.app.state.secured_editorial_projection_service


ProjectionDep = Annotated[
    SecuredEditorialProjectionService,
    Depends(get_projection),
]


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
