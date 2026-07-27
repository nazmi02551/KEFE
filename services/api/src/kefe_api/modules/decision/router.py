from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request
from pydantic import BaseModel, Field

from kefe_api.modules.decision.service import DecisionService
from kefe_api.modules.identity.dependencies import PrincipalDep

router = APIRouter(prefix="/v1", tags=["Decision"])


class CaseSummaryResponse(BaseModel):
    case_id: UUID
    case_version_id: UUID
    version_no: int
    title: str
    summary: str
    base_format: str
    primary_domain: str
    content_risk: str


class CaseListResponse(BaseModel):
    items: list[CaseSummaryResponse]


class QuestionResponse(BaseModel):
    question_id: UUID
    prompt: str
    response_type: str
    required: bool
    response_schema: dict[str, Any]
    options: list[str]


class CaseDetailResponse(BaseModel):
    case_id: UUID
    case_version_id: UUID
    version_no: int
    title: str
    summary: str
    base_format: str
    primary_domain: str
    content_risk: str
    questions: list[QuestionResponse]


class StartSessionResponse(BaseModel):
    session_id: UUID
    case_id: UUID
    case_version_id: UUID
    state: str


class ResponseItem(BaseModel):
    question_id: UUID
    value: Any


class UpdateResponsesRequest(BaseModel):
    responses: list[ResponseItem] = Field(min_length=1)


class UpdatePrivateReasonRequest(BaseModel):
    tags: list[str] = Field(default_factory=list, max_length=10)
    text: str | None = Field(default=None, max_length=1000)


class PrivateReasonResponse(BaseModel):
    session_id: UUID
    tags: list[str]
    text: str | None
    moderation_state: str
    visibility: str


class PerspectiveCardResponse(BaseModel):
    perspective_id: UUID
    slot: str
    body: str
    source_kind: str
    provenance_label: str
    moderation_state: str


class PerspectiveMethodologyResponse(BaseModel):
    mode: str
    sample_kind: str
    sample_size: int
    generated_at: datetime
    provenance_note: str


class PerspectiveResponse(BaseModel):
    session_id: UUID
    case_version_id: UUID
    cards: list[PerspectiveCardResponse] = Field(max_length=4)
    methodology: PerspectiveMethodologyResponse


def get_service(request: Request) -> DecisionService:
    return request.app.state.decision_service


DecisionServiceDep = Annotated[DecisionService, Depends(get_service)]
IdempotencyKey = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=8, max_length=128),
]


@router.get("/cases", response_model=CaseListResponse)
def list_cases(
    service: DecisionServiceDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> CaseListResponse:
    cases = service.list_cases(limit=limit)
    return CaseListResponse(
        items=[
            CaseSummaryResponse(
                case_id=case.case_id,
                case_version_id=case.id,
                version_no=case.version_no,
                title=case.title,
                summary=case.summary,
                base_format=case.base_format,
                primary_domain=case.primary_domain,
                content_risk=case.content_risk,
            )
            for case in cases
        ]
    )


@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
def get_case(case_id: UUID, service: DecisionServiceDep) -> CaseDetailResponse:
    case = service.get_case(case_id)
    return CaseDetailResponse(
        case_id=case.case_id,
        case_version_id=case.id,
        version_no=case.version_no,
        title=case.title,
        summary=case.summary,
        base_format=case.base_format,
        primary_domain=case.primary_domain,
        content_risk=case.content_risk,
        questions=[
            QuestionResponse(
                question_id=question.id,
                prompt=question.prompt,
                response_type=question.response_type,
                required=question.required,
                response_schema=dict(question.response_schema),
                options=list(question.options),
            )
            for question in case.questions
        ],
    )


@router.post("/cases/{case_id}/weigh-sessions", status_code=201)
def start_session(
    case_id: UUID,
    principal: PrincipalDep,
    service: DecisionServiceDep,
) -> StartSessionResponse:
    session = service.start_session(actor_id=principal.actor_id, case_id=case_id)
    return StartSessionResponse(
        session_id=session.id,
        case_id=session.case_id,
        case_version_id=session.case_version_id,
        state=session.state,
    )


@router.put("/weigh-sessions/{session_id}/responses")
def update_responses(
    session_id: UUID,
    body: UpdateResponsesRequest,
    principal: PrincipalDep,
    service: DecisionServiceDep,
) -> dict[str, Any]:
    session = service.update_responses(
        actor_id=principal.actor_id,
        session_id=session_id,
        responses={item.question_id: item.value for item in body.responses},
    )
    return {
        "session_id": session.id,
        "state": session.state,
        "response_count": len(session.responses),
    }


@router.put(
    "/weigh-sessions/{session_id}/reason",
    response_model=PrivateReasonResponse,
)
def update_private_reason(
    session_id: UUID,
    body: UpdatePrivateReasonRequest,
    principal: PrincipalDep,
    service: DecisionServiceDep,
) -> PrivateReasonResponse:
    reason = service.update_private_reason(
        actor_id=principal.actor_id,
        session_id=session_id,
        tags=body.tags,
        text=body.text,
    )
    return PrivateReasonResponse(
        session_id=reason.session_id,
        tags=list(reason.tags),
        text=reason.text,
        moderation_state=reason.moderation_state,
        visibility=reason.visibility,
    )


@router.post("/weigh-sessions/{session_id}/commit")
def commit(
    session_id: UUID,
    idempotency_key: IdempotencyKey,
    principal: PrincipalDep,
    service: DecisionServiceDep,
) -> dict[str, Any]:
    session = service.commit(
        actor_id=principal.actor_id,
        session_id=session_id,
        idempotency_key=idempotency_key,
    )
    return {
        "session_id": session.id,
        "state": session.state,
        "committed_at": session.committed_at,
        "reveal_available": True,
    }


@router.get("/weigh-sessions/{session_id}/reveal")
def reveal(
    session_id: UUID,
    principal: PrincipalDep,
    service: DecisionServiceDep,
) -> dict[str, Any]:
    snapshot = service.reveal(actor_id=principal.actor_id, session_id=session_id)
    return {
        "layer": snapshot.layer,
        "n": snapshot.n,
        "confidence": snapshot.confidence,
        "generated_at": snapshot.generated_at,
        "result": snapshot.payload,
    }


@router.get(
    "/weigh-sessions/{session_id}/perspectives",
    response_model=PerspectiveResponse,
)
def perspectives(
    session_id: UUID,
    principal: PrincipalDep,
    service: DecisionServiceDep,
) -> PerspectiveResponse:
    snapshot = service.perspectives(actor_id=principal.actor_id, session_id=session_id)
    return PerspectiveResponse(
        session_id=session_id,
        case_version_id=snapshot.case_version_id,
        cards=[
            PerspectiveCardResponse(
                perspective_id=card.perspective_id,
                slot=card.slot,
                body=card.body,
                source_kind=card.source_kind,
                provenance_label=card.provenance_label,
                moderation_state=card.moderation_state,
            )
            for card in snapshot.cards
        ],
        methodology=PerspectiveMethodologyResponse(
            mode=snapshot.mode,
            sample_kind=snapshot.sample_kind,
            sample_size=snapshot.sample_size,
            generated_at=snapshot.generated_at,
            provenance_note=snapshot.provenance_note,
        ),
    )
