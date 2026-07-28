from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from kefe_api.modules.flow_runtime.service import FlowRuntimeService
from kefe_api.modules.identity.dependencies import PrincipalDep

router = APIRouter(prefix="/v1", tags=["Flow Runtime"])


class FlowRuntimeStepResponse(BaseModel):
    code: str
    primitive_code: str
    capability_codes: list[str]
    next_step_codes: list[str]
    state: str
    reason_code: str | None


class FlowRuntimeResponse(BaseModel):
    session_id: UUID
    case_version_id: UUID
    session_state: str
    template_code: str
    template_version_no: int
    entry_step_code: str
    execution_support: str
    steps: list[FlowRuntimeStepResponse]


def get_service(request: Request) -> FlowRuntimeService:
    return request.app.state.flow_runtime_service


FlowRuntimeServiceDep = Annotated[FlowRuntimeService, Depends(get_service)]


@router.get(
    "/weigh-sessions/{session_id}/flow",
    response_model=FlowRuntimeResponse,
)
def get_flow_runtime(
    session_id: UUID,
    principal: PrincipalDep,
    service: FlowRuntimeServiceDep,
) -> FlowRuntimeResponse:
    snapshot = service.get_runtime(
        actor_id=principal.actor_id,
        session_id=session_id,
    )
    return FlowRuntimeResponse(
        session_id=snapshot.session_id,
        case_version_id=snapshot.case_version_id,
        session_state=snapshot.session_state,
        template_code=snapshot.template_code,
        template_version_no=snapshot.template_version_no,
        entry_step_code=snapshot.entry_step_code,
        execution_support=snapshot.execution_support.value,
        steps=[
            FlowRuntimeStepResponse(
                code=step.code,
                primitive_code=step.primitive_code,
                capability_codes=list(step.capability_codes),
                next_step_codes=list(step.next_step_codes),
                state=step.state.value,
                reason_code=step.reason_code,
            )
            for step in snapshot.steps
        ],
    )
