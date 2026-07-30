from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from kefe_api.modules.global_discovery.service import (
    GlobalDiscoveryService,
    LocalizedCaseView,
)

router = APIRouter(prefix="/v1/discovery", tags=["Global Discovery"])


class LocalizedOptionResponse(BaseModel):
    value: str
    label: str


class LocalizedQuestionResponse(BaseModel):
    question_id: UUID
    stable_code: str
    prompt: str
    response_type: str
    required: bool
    response_schema: dict[str, object]
    options: list[LocalizedOptionResponse]


class GlobalCaseSummaryResponse(BaseModel):
    case_id: UUID
    case_version_id: UUID
    version_no: int
    title: str
    summary: str
    base_format: str
    primary_domain: str
    content_risk: str
    requested_locale: str
    display_locale: str
    source_locale: str
    localized: bool
    market_scope: str
    country_codes: list[str]
    cultural_context_note: str | None
    legal_context_note: str | None


class GlobalCaseListResponse(BaseModel):
    items: list[GlobalCaseSummaryResponse]


class GlobalCaseDetailResponse(GlobalCaseSummaryResponse):
    questions: list[LocalizedQuestionResponse]


def get_service(request: Request) -> GlobalDiscoveryService:
    return request.app.state.global_discovery_service


GlobalDiscoveryServiceDep = Annotated[GlobalDiscoveryService, Depends(get_service)]


def _summary(view: LocalizedCaseView) -> GlobalCaseSummaryResponse:
    case = view.case
    return GlobalCaseSummaryResponse(
        case_id=case.case_id,
        case_version_id=case.id,
        version_no=case.version_no,
        title=view.title,
        summary=view.summary,
        base_format=case.base_format,
        primary_domain=case.primary_domain,
        content_risk=case.content_risk,
        requested_locale=view.requested_locale,
        display_locale=view.display_locale,
        source_locale=case.content_locale,
        localized=view.localized,
        market_scope=case.market_scope,
        country_codes=list(case.country_codes),
        cultural_context_note=view.cultural_context_note,
        legal_context_note=view.legal_context_note,
    )


@router.get("/cases", response_model=GlobalCaseListResponse)
def list_global_cases(
    service: GlobalDiscoveryServiceDep,
    locale: Annotated[str, Query(min_length=2, max_length=16)] = "tr-TR",
    country: Annotated[str | None, Query(min_length=2, max_length=2)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> GlobalCaseListResponse:
    views = service.list_cases(locale=locale, country=country, limit=limit)
    return GlobalCaseListResponse(items=[_summary(view) for view in views])


@router.get("/cases/{case_id}", response_model=GlobalCaseDetailResponse)
def get_global_case(
    case_id: UUID,
    service: GlobalDiscoveryServiceDep,
    locale: Annotated[str, Query(min_length=2, max_length=16)] = "tr-TR",
    country: Annotated[str | None, Query(min_length=2, max_length=2)] = None,
) -> GlobalCaseDetailResponse:
    view = service.get_case(case_id, locale=locale, country=country)
    summary = _summary(view)
    return GlobalCaseDetailResponse(
        **summary.model_dump(),
        questions=[
            LocalizedQuestionResponse(
                question_id=item.question.id,
                stable_code=item.question.stable_code,
                prompt=item.prompt,
                response_type=item.question.response_type,
                required=item.question.required,
                response_schema=dict(item.question.response_schema),
                options=[
                    LocalizedOptionResponse(value=value, label=label)
                    for value, label in item.option_labels.items()
                ],
            )
            for item in view.questions
        ],
    )
