from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel

from kefe_api.modules.decision.reflection_service import ReflectionService
from kefe_api.modules.identity.dependencies import PrincipalDep

router = APIRouter(prefix="/v1", tags=["Reflection"])


class ReflectionResponse(BaseModel):
    session_id: UUID
    case_version_id: UUID
    flow_step_code: str
    revision_count: int
    latest_revision_id: UUID
    latest_delta_id: UUID | None
    decision_changed: bool
    changed_question_count: int
    intervention_count: int
    intervention_type_codes: list[str]
    from_contribution_class: str | None
    to_contribution_class: str
    completed: bool


class ReflectionCompletionResponse(BaseModel):
    reflection_completion_id: UUID
    session_id: UUID
    case_version_id: UUID
    flow_step_code: str
    latest_revision_id: UUID
    latest_delta_id: UUID | None
    completed_at: datetime


def get_service(request: Request) -> ReflectionService:
    return request.app.state.reflection_service


ReflectionServiceDep = Annotated[ReflectionService, Depends(get_service)]
IdempotencyKey = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=8, max_length=128),
]


@router.get(
    "/weigh-sessions/{session_id}/reflection-steps/{step_code}",
    response_model=ReflectionResponse,
)
def get_reflection(
    session_id: UUID,
    step_code: str,
    principal: PrincipalDep,
    service: ReflectionServiceDep,
) -> ReflectionResponse:
    model = service.read(
        actor_id=principal.actor_id,
        session_id=session_id,
        flow_step_code=step_code,
    )
    return ReflectionResponse(
        session_id=model.session_id,
        case_version_id=model.case_version_id,
        flow_step_code=model.flow_step_code,
        revision_count=model.revision_count,
        latest_revision_id=model.latest_revision_id,
        latest_delta_id=model.latest_delta_id,
        decision_changed=model.decision_changed,
        changed_question_count=model.changed_question_count,
        intervention_count=model.intervention_count,
        intervention_type_codes=list(model.intervention_type_codes),
        from_contribution_class=model.from_contribution_class,
        to_contribution_class=model.to_contribution_class,
        completed=model.completed,
    )


@router.post(
    "/weigh-sessions/{session_id}/reflection-steps/{step_code}/complete",
    response_model=ReflectionCompletionResponse,
)
def complete_reflection(
    session_id: UUID,
    step_code: str,
    idempotency_key: IdempotencyKey,
    principal: PrincipalDep,
    service: ReflectionServiceDep,
) -> ReflectionCompletionResponse:
    completion = service.complete(
        actor_id=principal.actor_id,
        session_id=session_id,
        flow_step_code=step_code,
        idempotency_key=idempotency_key,
    )
    return ReflectionCompletionResponse(
        reflection_completion_id=completion.id,
        session_id=completion.session_id,
        case_version_id=completion.case_version_id,
        flow_step_code=completion.flow_step_code,
        latest_revision_id=completion.latest_revision_id,
        latest_delta_id=completion.latest_delta_id,
        completed_at=completion.completed_at,
    )
