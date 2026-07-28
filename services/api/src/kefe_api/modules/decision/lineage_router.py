from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel, Field

from kefe_api.modules.decision.lineage_service import DecisionLineageService
from kefe_api.modules.identity.dependencies import PrincipalDep

router = APIRouter(prefix="/v1", tags=["Decision Lineage"])


class RevisionResponseItem(BaseModel):
    question_id: UUID
    value: Any


class UpdateRevisionResponsesRequest(BaseModel):
    responses: list[RevisionResponseItem] = Field(min_length=1)


class UpdateRevisionReasonRequest(BaseModel):
    tags: list[str] = Field(default_factory=list, max_length=10)
    text: str | None = Field(default=None, max_length=1000)


class RevisionDraftResponse(BaseModel):
    session_id: UUID
    flow_step_code: str
    response_count: int
    has_private_reason: bool
    updated_at: datetime


class ExposureResponse(BaseModel):
    exposure_id: UUID
    session_id: UUID
    sequence_no: int
    flow_step_code: str
    resource_category: str
    primitive_code: str
    capability_codes: list[str]
    occurred_at: datetime
    intervention_id: UUID | None = None


class RevisionCommitResponse(BaseModel):
    revision_id: UUID
    session_id: UUID
    revision_no: int
    flow_step_code: str
    contribution_class: str
    committed_at: datetime
    delta_id: UUID | None = None


class RevisionSummaryResponse(BaseModel):
    revision_id: UUID
    revision_no: int
    flow_step_code: str
    contribution_class: str
    exposure_sequence_at_commit: int
    committed_at: datetime


class ExposureSummaryResponse(BaseModel):
    exposure_id: UUID
    sequence_no: int
    flow_step_code: str
    resource_category: str
    primitive_code: str
    occurred_at: datetime


class InterventionSummaryResponse(BaseModel):
    intervention_id: UUID
    exposure_id: UUID | None
    type_code: str
    occurred_at: datetime


class DeltaSummaryResponse(BaseModel):
    delta_id: UUID
    from_revision_id: UUID
    to_revision_id: UUID
    intervention_ids: list[UUID]
    changed_question_ids: list[UUID]
    changed_count: int
    created_at: datetime


class LineageResponse(BaseModel):
    session_id: UUID
    case_version_id: UUID
    revisions: list[RevisionSummaryResponse]
    exposures: list[ExposureSummaryResponse]
    interventions: list[InterventionSummaryResponse]
    deltas: list[DeltaSummaryResponse]


def get_service(request: Request) -> DecisionLineageService:
    return request.app.state.decision_lineage_service


LineageServiceDep = Annotated[DecisionLineageService, Depends(get_service)]
IdempotencyKey = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=8, max_length=128),
]


@router.post(
    "/weigh-sessions/{session_id}/flow-steps/{step_code}/exposures",
    response_model=ExposureResponse,
    status_code=201,
)
def record_flow_step_exposure(
    session_id: UUID,
    step_code: str,
    idempotency_key: IdempotencyKey,
    principal: PrincipalDep,
    service: LineageServiceDep,
) -> ExposureResponse:
    exposure, intervention = service.record_flow_step_exposure(
        actor_id=principal.actor_id,
        session_id=session_id,
        flow_step_code=step_code,
        idempotency_key=idempotency_key,
    )
    return ExposureResponse(
        exposure_id=exposure.id,
        session_id=exposure.session_id,
        sequence_no=exposure.sequence_no,
        flow_step_code=exposure.flow_step_code,
        resource_category=exposure.resource_category,
        primitive_code=exposure.primitive_code,
        capability_codes=list(exposure.capability_codes),
        occurred_at=exposure.occurred_at,
        intervention_id=intervention.id if intervention else None,
    )


@router.put(
    "/weigh-sessions/{session_id}/decision-steps/{step_code}/responses",
    response_model=RevisionDraftResponse,
)
def update_revision_responses(
    session_id: UUID,
    step_code: str,
    body: UpdateRevisionResponsesRequest,
    principal: PrincipalDep,
    service: LineageServiceDep,
) -> RevisionDraftResponse:
    draft = service.update_revision_responses(
        actor_id=principal.actor_id,
        session_id=session_id,
        flow_step_code=step_code,
        responses={item.question_id: item.value for item in body.responses},
    )
    return RevisionDraftResponse(
        session_id=draft.session_id,
        flow_step_code=draft.flow_step_code,
        response_count=len(draft.responses),
        has_private_reason=draft.reason_snapshot is not None,
        updated_at=draft.updated_at,
    )


@router.put(
    "/weigh-sessions/{session_id}/decision-steps/{step_code}/reason",
    response_model=RevisionDraftResponse,
)
def update_revision_reason(
    session_id: UUID,
    step_code: str,
    body: UpdateRevisionReasonRequest,
    principal: PrincipalDep,
    service: LineageServiceDep,
) -> RevisionDraftResponse:
    draft = service.update_revision_reason(
        actor_id=principal.actor_id,
        session_id=session_id,
        flow_step_code=step_code,
        tags=body.tags,
        text=body.text,
    )
    return RevisionDraftResponse(
        session_id=draft.session_id,
        flow_step_code=draft.flow_step_code,
        response_count=len(draft.responses),
        has_private_reason=draft.reason_snapshot is not None,
        updated_at=draft.updated_at,
    )


@router.post(
    "/weigh-sessions/{session_id}/decision-steps/{step_code}/commit",
    response_model=RevisionCommitResponse,
)
def commit_revision(
    session_id: UUID,
    step_code: str,
    idempotency_key: IdempotencyKey,
    principal: PrincipalDep,
    service: LineageServiceDep,
) -> RevisionCommitResponse:
    attempt = service.commit_revision(
        actor_id=principal.actor_id,
        session_id=session_id,
        flow_step_code=step_code,
        idempotency_key=idempotency_key,
    )
    revision = attempt.revision
    assert revision is not None
    return RevisionCommitResponse(
        revision_id=revision.id,
        session_id=revision.session_id,
        revision_no=revision.revision_no,
        flow_step_code=revision.flow_step_code,
        contribution_class=revision.contribution_class.value,
        committed_at=revision.committed_at,
        delta_id=attempt.delta.id if attempt.delta else None,
    )


@router.get(
    "/weigh-sessions/{session_id}/lineage",
    response_model=LineageResponse,
)
def get_lineage(
    session_id: UUID,
    principal: PrincipalDep,
    service: LineageServiceDep,
) -> LineageResponse:
    snapshot = service.lineage(actor_id=principal.actor_id, session_id=session_id)
    return LineageResponse(
        session_id=snapshot.session_id,
        case_version_id=snapshot.case_version_id,
        revisions=[
            RevisionSummaryResponse(
                revision_id=item.id,
                revision_no=item.revision_no,
                flow_step_code=item.flow_step_code,
                contribution_class=item.contribution_class.value,
                exposure_sequence_at_commit=item.exposure_sequence_at_commit,
                committed_at=item.committed_at,
            )
            for item in snapshot.revisions
        ],
        exposures=[
            ExposureSummaryResponse(
                exposure_id=item.id,
                sequence_no=item.sequence_no,
                flow_step_code=item.flow_step_code,
                resource_category=item.resource_category,
                primitive_code=item.primitive_code,
                occurred_at=item.occurred_at,
            )
            for item in snapshot.exposures
        ],
        interventions=[
            InterventionSummaryResponse(
                intervention_id=item.id,
                exposure_id=item.exposure_id,
                type_code=item.type_code,
                occurred_at=item.occurred_at,
            )
            for item in snapshot.interventions
        ],
        deltas=[
            DeltaSummaryResponse(
                delta_id=item.id,
                from_revision_id=item.from_revision_id,
                to_revision_id=item.to_revision_id,
                intervention_ids=list(item.intervention_ids),
                changed_question_ids=[
                    UUID(value) for value in item.diff_snapshot.get("changed_question_ids", [])
                ],
                changed_count=int(item.diff_snapshot.get("changed_count", 0)),
                created_at=item.created_at,
            )
            for item in snapshot.deltas
        ],
    )
