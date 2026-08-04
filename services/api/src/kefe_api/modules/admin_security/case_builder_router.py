from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.admin_security.router import (
    AuthoringDep,
    ReadPrincipalDep,
    WritePrincipalDep,
)
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseLocalization,
    AuthoringCaseVersion,
    AuthoringContextBlock,
    AuthoringIssue,
    AuthoringQuestion,
    AuthoringSourceReference,
    MarketScope,
)

router = APIRouter(
    prefix="/internal/admin/v1/case-builder",
    tags=["Internal Admin Case Builder"],
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CaseBuilderQuestionInput(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    stable_code: str = Field(min_length=1, max_length=120)
    prompt: str = Field(min_length=1, max_length=2000)
    response_type: str = Field(min_length=1, max_length=80)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_required: bool = True
    sort_order: int = 0

    def to_domain(self) -> AuthoringQuestion:
        return AuthoringQuestion(
            id=self.id,
            stable_code=self.stable_code,
            prompt=self.prompt,
            response_type=self.response_type,
            response_schema=self.response_schema,
            is_active=self.is_active,
            is_required=self.is_required,
            sort_order=self.sort_order,
        )


class CaseBuilderIssueInput(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    code: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=500)
    questions: list[CaseBuilderQuestionInput] = Field(default_factory=list)
    sort_order: int = 0

    def to_domain(self) -> AuthoringIssue:
        return AuthoringIssue(
            id=self.id,
            code=self.code,
            title=self.title,
            questions=tuple(question.to_domain() for question in self.questions),
            sort_order=self.sort_order,
        )


class CaseBuilderSourceInput(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    source_kind: str = Field(min_length=1, max_length=80)
    locator: str = Field(min_length=1, max_length=4000)
    title: str = Field(min_length=1, max_length=1000)
    publisher: str = Field(default="", max_length=500)
    published_at: datetime | None = None
    claim_status: str | None = Field(default=None, max_length=80)
    verified: bool = False

    def to_domain(self) -> AuthoringSourceReference:
        return AuthoringSourceReference(
            id=self.id,
            source_kind=self.source_kind,
            locator=self.locator,
            title=self.title,
            publisher=self.publisher,
            published_at=self.published_at,
            claim_status=self.claim_status,
            verified=self.verified,
        )


class CaseBuilderContextBlockInput(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1, max_length=1000)
    body: str = Field(min_length=1, max_length=20000)
    disclosure_level: str = Field(min_length=1, max_length=80)
    claim_status: str = Field(min_length=1, max_length=80)
    source_ids: list[UUID] = Field(default_factory=list)
    sort_order: int = 0
    block_type: str = Field(default="CONTEXT", min_length=1, max_length=80)

    def to_domain(self) -> AuthoringContextBlock:
        return AuthoringContextBlock(
            id=self.id,
            title=self.title,
            body=self.body,
            disclosure_level=self.disclosure_level,
            claim_status=self.claim_status,
            source_ids=tuple(self.source_ids),
            sort_order=self.sort_order,
            block_type=self.block_type,
        )


class CaseBuilderLocalizationInput(StrictModel):
    locale: str = Field(min_length=2, max_length=35)
    title: str = Field(min_length=1, max_length=1000)
    summary: str = Field(min_length=1, max_length=5000)
    question_prompts: dict[str, str] = Field(default_factory=dict)
    option_labels: dict[str, dict[str, str]] = Field(default_factory=dict)
    cultural_context_note: str | None = Field(default=None, max_length=5000)
    legal_context_note: str | None = Field(default=None, max_length=5000)

    def to_domain(self) -> AuthoringCaseLocalization:
        return AuthoringCaseLocalization(
            locale=self.locale,
            title=self.title,
            summary=self.summary,
            question_prompts=self.question_prompts,
            option_labels=self.option_labels,
            cultural_context_note=self.cultural_context_note,
            legal_context_note=self.legal_context_note,
        )


class CaseBuilderDraftInput(StrictModel):
    title: str = Field(min_length=1, max_length=1000)
    summary: str = Field(min_length=1, max_length=5000)
    base_format_code: str = Field(min_length=1, max_length=80)
    primary_domain_code: str = Field(min_length=1, max_length=120)
    content_risk: str = Field(min_length=1, max_length=20)
    issues: list[CaseBuilderIssueInput] = Field(default_factory=list)
    context_blocks: list[CaseBuilderContextBlockInput] = Field(default_factory=list)
    sources: list[CaseBuilderSourceInput] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    is_fact_bearing: bool = False
    is_real_event: bool = False
    required_review_modes: list[str] = Field(default_factory=list)
    content_locale: str = Field(min_length=2, max_length=35)
    market_scope: MarketScope
    country_codes: list[str] = Field(default_factory=list)
    cultural_context_note: str | None = Field(default=None, max_length=5000)
    legal_context_note: str | None = Field(default=None, max_length=5000)
    localizations: list[CaseBuilderLocalizationInput] = Field(default_factory=list)

    def apply_to(self, version: AuthoringCaseVersion) -> AuthoringCaseVersion:
        return replace(
            version,
            title=self.title,
            summary=self.summary,
            base_format_code=self.base_format_code,
            primary_domain_code=self.primary_domain_code,
            content_risk=self.content_risk,
            issues=tuple(issue.to_domain() for issue in self.issues),
            context_blocks=tuple(block.to_domain() for block in self.context_blocks),
            sources=tuple(source.to_domain() for source in self.sources),
            modifiers=tuple(self.modifiers),
            is_fact_bearing=self.is_fact_bearing,
            is_real_event=self.is_real_event,
            required_review_modes=tuple(self.required_review_modes),
            content_locale=self.content_locale,
            market_scope=self.market_scope,
            country_codes=tuple(self.country_codes),
            cultural_context_note=self.cultural_context_note,
            legal_context_note=self.legal_context_note,
            localizations=tuple(item.to_domain() for item in self.localizations),
        )


class CaseBuilderQuestionResponse(StrictModel):
    id: UUID
    stable_code: str
    prompt: str
    response_type: str
    response_schema: dict[str, Any]
    is_active: bool
    is_required: bool
    sort_order: int


class CaseBuilderIssueResponse(StrictModel):
    id: UUID
    code: str
    title: str
    questions: list[CaseBuilderQuestionResponse]
    sort_order: int


class CaseBuilderContextBlockResponse(StrictModel):
    id: UUID
    title: str
    body: str
    disclosure_level: str
    claim_status: str
    source_ids: list[UUID]
    sort_order: int
    block_type: str


class CaseBuilderSourceResponse(StrictModel):
    id: UUID
    source_kind: str
    locator: str
    title: str
    publisher: str
    published_at: datetime | None
    claim_status: str | None
    verified: bool


class CaseBuilderLocalizationResponse(StrictModel):
    locale: str
    title: str
    summary: str
    question_prompts: dict[str, str]
    option_labels: dict[str, dict[str, str]]
    cultural_context_note: str | None
    legal_context_note: str | None


class CaseBuilderVersionResponse(StrictModel):
    id: UUID
    case_id: UUID
    version_no: int
    state: str
    title: str
    summary: str
    base_format_code: str
    primary_domain_code: str
    content_risk: str
    issues: list[CaseBuilderIssueResponse]
    context_blocks: list[CaseBuilderContextBlockResponse]
    sources: list[CaseBuilderSourceResponse]
    modifiers: list[str]
    is_fact_bearing: bool
    is_real_event: bool
    required_review_modes: list[str]
    completed_review_modes: list[str]
    flow_template_code: str
    flow_template_version_no: int
    content_locale: str
    market_scope: str
    country_codes: list[str]
    cultural_context_note: str | None
    legal_context_note: str | None
    localizations: list[CaseBuilderLocalizationResponse]
    created_at: datetime
    published_at: datetime | None


@router.get(
    "/case-versions/{version_id}",
    response_model=CaseBuilderVersionResponse,
)
def get_case_builder_version(
    version_id: UUID,
    principal: ReadPrincipalDep,
    authoring: AuthoringDep,
) -> CaseBuilderVersionResponse:
    return _version_response(authoring.draft_for_edit(principal, version_id))


@router.put(
    "/case-versions/{version_id}",
    response_model=CaseBuilderVersionResponse,
)
def save_case_builder_draft(
    version_id: UUID,
    body: CaseBuilderDraftInput,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> CaseBuilderVersionResponse:
    current = authoring.draft_for_edit(principal, version_id)
    updated = body.apply_to(current)
    return _version_response(authoring.save_draft(principal, updated))


def _version_response(version: AuthoringCaseVersion) -> CaseBuilderVersionResponse:
    return CaseBuilderVersionResponse(
        id=version.id,
        case_id=version.case_id,
        version_no=version.version_no,
        state=version.state.value,
        title=version.title,
        summary=version.summary,
        base_format_code=version.base_format_code,
        primary_domain_code=version.primary_domain_code,
        content_risk=version.content_risk,
        issues=[
            CaseBuilderIssueResponse(
                id=issue.id,
                code=issue.code,
                title=issue.title,
                questions=[
                    CaseBuilderQuestionResponse(
                        id=question.id,
                        stable_code=question.stable_code,
                        prompt=question.prompt,
                        response_type=question.response_type,
                        response_schema=question.response_schema,
                        is_active=question.is_active,
                        is_required=question.is_required,
                        sort_order=question.sort_order,
                    )
                    for question in issue.questions
                ],
                sort_order=issue.sort_order,
            )
            for issue in version.issues
        ],
        context_blocks=[
            CaseBuilderContextBlockResponse(
                id=block.id,
                title=block.title,
                body=block.body,
                disclosure_level=block.disclosure_level,
                claim_status=block.claim_status,
                source_ids=list(block.source_ids),
                sort_order=block.sort_order,
                block_type=block.block_type,
            )
            for block in version.context_blocks
        ],
        sources=[
            CaseBuilderSourceResponse(
                id=source.id,
                source_kind=source.source_kind,
                locator=source.locator,
                title=source.title,
                publisher=source.publisher,
                published_at=source.published_at,
                claim_status=source.claim_status,
                verified=source.verified,
            )
            for source in version.sources
        ],
        modifiers=list(version.modifiers),
        is_fact_bearing=version.is_fact_bearing,
        is_real_event=version.is_real_event,
        required_review_modes=list(version.required_review_modes),
        completed_review_modes=list(version.completed_review_modes),
        flow_template_code=version.flow_template_code,
        flow_template_version_no=version.flow_template_version_no,
        content_locale=version.content_locale,
        market_scope=version.market_scope.value,
        country_codes=list(version.country_codes),
        cultural_context_note=version.cultural_context_note,
        legal_context_note=version.legal_context_note,
        localizations=[
            CaseBuilderLocalizationResponse(
                locale=item.locale,
                title=item.title,
                summary=item.summary,
                question_prompts=item.question_prompts,
                option_labels=item.option_labels,
                cultural_context_note=item.cultural_context_note,
                legal_context_note=item.legal_context_note,
            )
            for item in version.localizations
        ],
        created_at=version.created_at,
        published_at=version.published_at,
    )
