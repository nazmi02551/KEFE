from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.candidate_bundle import (
    SecuredCandidateBundleService,
)
from kefe_api.modules.admin_security.router import StrictModel, WritePrincipalDep
from kefe_api.modules.admin_security.source_brief_review_router import (
    get_source_brief_review,
)
from kefe_api.modules.content_authoring.models import MarketScope
from kefe_api.modules.ingestion_orchestration.candidate_case_bundle import (
    CandidateCaseBundleStageProcessor,
    CandidateCaseEditorialConfiguration,
)

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class CandidateBundleRequest(StrictModel):
    source_brief_review_decision_id: UUID
    slug: str
    title: str
    summary: str
    base_format_code: str
    primary_domain_code: str
    content_risk: str
    issue_code: str
    issue_title: str
    question_stable_code: str
    question_prompt: str
    response_options: list[str]
    flow_template_code: str
    flow_template_version_no: int
    content_locale: str
    market_scope: str
    country_codes: list[str]
    required_review_modes: list[str]
    is_fact_bearing: bool
    is_real_event: bool
    context_title: str
    cultural_context_note: str | None = None
    legal_context_note: str | None = None


class CandidateBundleResponse(StrictModel):
    candidate_seed_artifact_id: UUID
    run_id: UUID
    decision_problem_proposal_id: UUID
    question_draft_proposal_id: UUID
    candidate_case_proposal_id: UUID
    run_state: str
    proposal_review_state: str


def get_candidate_bundle_service(request: Request) -> SecuredCandidateBundleService:
    repository = request.app.state.ingestion_orchestration_repository
    knowledge = request.app.state.knowledge_repository
    return SecuredCandidateBundleService(
        security=request.app.state.admin_security_service,
        source_briefs=get_source_brief_review(request),
        ingestion=request.app.state.ingestion_orchestration_service,
        repository=repository,
        knowledge=knowledge,
        processor=CandidateCaseBundleStageProcessor(
            knowledge=knowledge,
            repository=repository,
        ),
    )


CandidateBundleDep = Annotated[
    SecuredCandidateBundleService,
    Depends(get_candidate_bundle_service),
]


def _configuration(payload: CandidateBundleRequest) -> CandidateCaseEditorialConfiguration:
    try:
        return CandidateCaseEditorialConfiguration(
            slug=payload.slug,
            title=payload.title,
            summary=payload.summary,
            base_format_code=payload.base_format_code,
            primary_domain_code=payload.primary_domain_code,
            content_risk=payload.content_risk,
            issue_code=payload.issue_code,
            issue_title=payload.issue_title,
            question_stable_code=payload.question_stable_code,
            question_prompt=payload.question_prompt,
            response_options=tuple(payload.response_options),
            flow_template_code=payload.flow_template_code,
            flow_template_version_no=payload.flow_template_version_no,
            content_locale=payload.content_locale,
            market_scope=MarketScope(payload.market_scope),
            country_codes=tuple(payload.country_codes),
            required_review_modes=tuple(payload.required_review_modes),
            is_fact_bearing=payload.is_fact_bearing,
            is_real_event=payload.is_real_event,
            context_title=payload.context_title,
            cultural_context_note=payload.cultural_context_note,
            legal_context_note=payload.legal_context_note,
        )
    except ValueError as exc:
        raise DomainError(
            "ADMIN_CANDIDATE_BUNDLE_CONFIGURATION_INVALID",
            "Candidate bundle editorial configuration is invalid",
            422,
        ) from exc


@router.post(
    "/source-briefs/{proposal_id}/candidate-bundle",
    response_model=CandidateBundleResponse,
)
def build_candidate_bundle(
    proposal_id: UUID,
    payload: CandidateBundleRequest,
    principal: WritePrincipalDep,
    service: CandidateBundleDep,
) -> CandidateBundleResponse:
    result = service.build(
        principal,
        source_brief_proposal_id=proposal_id,
        source_brief_review_decision_id=payload.source_brief_review_decision_id,
        configuration=_configuration(payload),
    )
    return CandidateBundleResponse(
        candidate_seed_artifact_id=result.candidate_seed_artifact_id,
        run_id=result.run_id,
        decision_problem_proposal_id=result.proposal_ids[0],
        question_draft_proposal_id=result.proposal_ids[1],
        candidate_case_proposal_id=result.proposal_ids[2],
        run_state=result.run_state.value,
        proposal_review_state="PENDING",
    )


__all__ = ["router"]
