from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Request, status
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.content_authoring import SecuredContentAuthoringService
from kefe_api.modules.admin_security.models import AdminPrincipal
from kefe_api.modules.admin_security.ports import AdminCsrfVerifier
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    AuthoringContextBlock,
    AuthoringIssue,
    AuthoringQuestion,
    AuthoringSourceReference,
    CaseIdentity,
    ContentLifecycle,
    LifecycleAuditEntry,
)

ADMIN_SESSION_COOKIE = "kefe_admin_session"
ADMIN_CSRF_HEADER = "X-KEFE-CSRF"

router = APIRouter(prefix="/internal/admin/v1", tags=["Internal Admin"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QuestionInput(StrictModel):
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


class IssueInput(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    code: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=500)
    questions: list[QuestionInput] = Field(default_factory=list)
    sort_order: int = 0

    def to_domain(self) -> AuthoringIssue:
        return AuthoringIssue(
            id=self.id,
            code=self.code,
            title=self.title,
            questions=tuple(question.to_domain() for question in self.questions),
            sort_order=self.sort_order,
        )


class SourceInput(StrictModel):
    id: UUID = Field(default_factory=uuid4)
    source_kind: str = Field(min_length=1, max_length=80)
    locator: str = Field(min_length=1, max_length=4000)
    title: str = Field(min_length=1, max_length=1000)
    publisher: str = Field(default="", max_length=500)
    published_at: datetime | None = None
    claim_status: str | None = None
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


class ContextBlockInput(StrictModel):
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


class DraftContentInput(StrictModel):
    title: str = Field(min_length=1, max_length=1000)
    summary: str = Field(min_length=1, max_length=5000)
    base_format_code: str = Field(min_length=1, max_length=80)
    primary_domain_code: str = Field(min_length=1, max_length=120)
    content_risk: str = Field(min_length=1, max_length=20)
    issues: list[IssueInput] = Field(default_factory=list)
    context_blocks: list[ContextBlockInput] = Field(default_factory=list)
    sources: list[SourceInput] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    is_fact_bearing: bool = False
    is_real_event: bool = False
    required_review_modes: list[str] = Field(default_factory=list)
    completed_review_modes: list[str] = Field(default_factory=list)

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
            completed_review_modes=tuple(self.completed_review_modes),
        )


class CreateCaseRequest(StrictModel):
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    content: DraftContentInput


class RationaleRequest(StrictModel):
    rationale: str = Field(min_length=1, max_length=5000)


class AdminSessionResponse(StrictModel):
    admin_subject_id: UUID
    session_id: UUID
    roles: list[str]
    direct_capabilities: list[str]
    authenticated_at: datetime
    mfa_satisfied_at: datetime | None
    step_up_at: datetime | None
    expires_at: datetime


class QuestionResponse(StrictModel):
    id: UUID
    stable_code: str
    prompt: str
    response_type: str
    response_schema: dict[str, Any]
    is_active: bool
    is_required: bool
    sort_order: int


class IssueResponse(StrictModel):
    id: UUID
    code: str
    title: str
    questions: list[QuestionResponse]
    sort_order: int


class ContextBlockResponse(StrictModel):
    id: UUID
    title: str
    body: str
    disclosure_level: str
    claim_status: str
    source_ids: list[UUID]
    sort_order: int
    block_type: str


class SourceResponse(StrictModel):
    id: UUID
    source_kind: str
    locator: str
    title: str
    publisher: str
    published_at: datetime | None
    claim_status: str | None
    verified: bool


class AuthoringVersionResponse(StrictModel):
    id: UUID
    case_id: UUID
    version_no: int
    state: str
    title: str
    summary: str
    base_format_code: str
    primary_domain_code: str
    content_risk: str
    issues: list[IssueResponse]
    context_blocks: list[ContextBlockResponse]
    sources: list[SourceResponse]
    modifiers: list[str]
    is_fact_bearing: bool
    is_real_event: bool
    required_review_modes: list[str]
    completed_review_modes: list[str]
    created_at: datetime
    published_at: datetime | None


class AuditEntryResponse(StrictModel):
    audit_id: UUID
    case_id: UUID
    case_version_id: UUID
    actor_ref: str
    command: str
    previous_state: str | None
    new_state: str
    rationale: str | None
    occurred_at: datetime


class AuditTrailResponse(StrictModel):
    items: list[AuditEntryResponse]


def get_security(request: Request) -> AdminSecurityService:
    return request.app.state.admin_security_service


def get_csrf_verifier(request: Request) -> AdminCsrfVerifier:
    return request.app.state.admin_csrf_verifier


def get_authoring(request: Request) -> SecuredContentAuthoringService:
    return request.app.state.secured_content_authoring_service


def read_principal(request: Request) -> AdminPrincipal:
    security = get_security(request)
    return security.authenticate(request.cookies.get(ADMIN_SESSION_COOKIE))


def write_principal(
    request: Request,
    csrf_token: Annotated[str | None, Header(alias=ADMIN_CSRF_HEADER)] = None,
) -> AdminPrincipal:
    session_token = request.cookies.get(ADMIN_SESSION_COOKIE)
    security = get_security(request)
    principal = security.resolve_session(session_token)

    if not csrf_token:
        raise DomainError("ADMIN_CSRF_REQUIRED", "Admin CSRF token is required", 403)
    if session_token is None or not get_csrf_verifier(request).verify(
        session_token=session_token,
        csrf_token=csrf_token,
    ):
        raise DomainError("ADMIN_CSRF_INVALID", "Admin CSRF token is invalid", 403)

    security.touch(principal)
    return principal


ReadPrincipalDep = Annotated[AdminPrincipal, Depends(read_principal)]
WritePrincipalDep = Annotated[AdminPrincipal, Depends(write_principal)]
AuthoringDep = Annotated[SecuredContentAuthoringService, Depends(get_authoring)]


@router.get("/session", response_model=AdminSessionResponse)
def session(principal: ReadPrincipalDep) -> AdminSessionResponse:
    return AdminSessionResponse(
        admin_subject_id=principal.admin_subject_id,
        session_id=principal.session_id,
        roles=sorted(role.value for role in principal.roles),
        direct_capabilities=sorted(item.value for item in principal.direct_capabilities),
        authenticated_at=principal.authenticated_at,
        mfa_satisfied_at=principal.mfa_satisfied_at,
        step_up_at=principal.step_up_at,
        expires_at=principal.expires_at,
    )


@router.post(
    "/cases",
    response_model=AuthoringVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_case(
    body: CreateCaseRequest,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> AuthoringVersionResponse:
    identity = CaseIdentity(id=uuid4(), slug=body.slug)
    initial = body.content.apply_to(
        AuthoringCaseVersion(
            id=uuid4(),
            case_id=identity.id,
            version_no=1,
            state=ContentLifecycle.DRAFT,
            title=body.content.title,
            summary=body.content.summary,
            base_format_code=body.content.base_format_code,
            primary_domain_code=body.content.primary_domain_code,
            content_risk=body.content.content_risk,
            issues=(),
        )
    )
    created = authoring.create_case(principal, identity=identity, initial_version=initial)
    return _version_response(created)


@router.post(
    "/case-versions/{version_id}/revisions",
    response_model=AuthoringVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_revision(
    version_id: UUID,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> AuthoringVersionResponse:
    return _version_response(
        authoring.create_revision(principal, source_version_id=version_id)
    )


@router.put("/case-versions/{version_id}", response_model=AuthoringVersionResponse)
def save_draft(
    version_id: UUID,
    body: DraftContentInput,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> AuthoringVersionResponse:
    current = authoring.draft_for_edit(principal, version_id)
    updated = body.apply_to(current)
    return _version_response(authoring.save_draft(principal, updated))


@router.post("/case-versions/{version_id}/submit", response_model=AuthoringVersionResponse)
def submit_for_review(
    version_id: UUID,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> AuthoringVersionResponse:
    return _version_response(authoring.submit_for_review(principal, version_id))


@router.post("/case-versions/{version_id}/approve", response_model=AuthoringVersionResponse)
def approve(
    version_id: UUID,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> AuthoringVersionResponse:
    return _version_response(authoring.approve(principal, version_id))


@router.post("/case-versions/{version_id}/reject", response_model=AuthoringVersionResponse)
def reject(
    version_id: UUID,
    body: RationaleRequest,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> AuthoringVersionResponse:
    return _version_response(
        authoring.reject(principal, version_id, rationale=body.rationale)
    )


@router.post("/case-versions/{version_id}/publish", response_model=AuthoringVersionResponse)
def publish(
    version_id: UUID,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> AuthoringVersionResponse:
    return _version_response(authoring.publish(principal, version_id))


@router.post("/case-versions/{version_id}/withdraw", response_model=AuthoringVersionResponse)
def withdraw(
    version_id: UUID,
    body: RationaleRequest,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> AuthoringVersionResponse:
    return _version_response(
        authoring.withdraw(principal, version_id, rationale=body.rationale)
    )


@router.get("/cases/{case_id}/audit", response_model=AuditTrailResponse)
def audit_trail(
    case_id: UUID,
    principal: ReadPrincipalDep,
    authoring: AuthoringDep,
) -> AuditTrailResponse:
    entries = authoring.audit_trail(principal, case_id)
    return AuditTrailResponse(items=[_audit_response(entry) for entry in entries])


def _version_response(version: AuthoringCaseVersion) -> AuthoringVersionResponse:
    return AuthoringVersionResponse(
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
            IssueResponse(
                id=issue.id,
                code=issue.code,
                title=issue.title,
                questions=[
                    QuestionResponse(
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
            ContextBlockResponse(
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
            SourceResponse(
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
        created_at=version.created_at,
        published_at=version.published_at,
    )


def _audit_response(entry: LifecycleAuditEntry) -> AuditEntryResponse:
    return AuditEntryResponse(
        audit_id=entry.audit_id,
        case_id=entry.case_id,
        case_version_id=entry.case_version_id,
        actor_ref=entry.actor_ref,
        command=entry.command,
        previous_state=entry.previous_state.value if entry.previous_state else None,
        new_state=entry.new_state.value,
        rationale=entry.rationale,
        occurred_at=entry.occurred_at,
    )
