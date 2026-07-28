from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

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
)

ADMIN_SESSION_COOKIE = "kefe_admin_session"
ADMIN_CSRF_HEADER = "X-KEFE-CSRF"

router = APIRouter(prefix="/v1")


class QuestionInput(BaseModel):
    id: UUID
    stable_code: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=1, max_length=2000)
    response_type: str = Field(min_length=1, max_length=100)
    response_schema: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_required: bool = True
    sort_order: int = Field(default=0, ge=0)


class IssueInput(BaseModel):
    id: UUID
    code: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    questions: list[QuestionInput] = Field(min_length=1)
    sort_order: int = Field(default=0, ge=0)


class SourceInput(BaseModel):
    id: UUID
    source_kind: str = Field(min_length=1, max_length=100)
    locator: str = Field(min_length=1, max_length=4000)
    title: str = Field(min_length=1, max_length=1000)
    publisher: str = Field(default="", max_length=500)
    published_at: datetime | None = None
    claim_status: str | None = Field(default=None, max_length=100)
    verified: bool = False


class ContextBlockInput(BaseModel):
    id: UUID
    title: str = Field(min_length=1, max_length=1000)
    body: str = Field(min_length=1, max_length=10000)
    disclosure_level: str = Field(min_length=1, max_length=100)
    claim_status: str = Field(min_length=1, max_length=100)
    source_ids: list[UUID] = Field(default_factory=list)
    sort_order: int = Field(default=0, ge=0)
    block_type: str = Field(default="CONTEXT", min_length=1, max_length=100)


class VersionDraftInput(BaseModel):
    title: str = Field(min_length=1, max_length=1000)
    summary: str = Field(min_length=1, max_length=5000)
    base_format_code: str = Field(min_length=1, max_length=100)
    primary_domain_code: str = Field(min_length=1, max_length=100)
    content_risk: str = Field(min_length=1, max_length=20)
    issues: list[IssueInput] = Field(min_length=1)
    context_blocks: list[ContextBlockInput] = Field(default_factory=list)
    sources: list[SourceInput] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    is_fact_bearing: bool = False
    is_real_event: bool = False
    required_review_modes: list[str] = Field(default_factory=list)
    completed_review_modes: list[str] = Field(default_factory=list)


class CreateCaseRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=200, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    version: VersionDraftInput


class RationaleRequest(BaseModel):
    rationale: str = Field(min_length=1, max_length=2000)


class VersionResponse(BaseModel):
    case_id: UUID
    version_id: UUID
    version_no: int
    state: str
    title: str
    published_at: datetime | None


class AuditEntryResponse(BaseModel):
    audit_id: UUID
    case_id: UUID
    case_version_id: UUID
    actor_ref: str
    command: str
    previous_state: str | None
    new_state: str
    rationale: str | None
    occurred_at: datetime


class AuditTrailResponse(BaseModel):
    items: list[AuditEntryResponse]


def _security(request: Request) -> AdminSecurityService:
    return request.app.state.admin_security_service


def _csrf(request: Request) -> AdminCsrfVerifier:
    return request.app.state.admin_csrf_verifier


def _authoring(request: Request) -> SecuredContentAuthoringService:
    return request.app.state.secured_content_authoring


def _admin_principal(request: Request) -> AdminPrincipal:
    token = request.cookies.get(ADMIN_SESSION_COOKIE)
    return _security(request).authenticate(token)


def _admin_state_change_principal(request: Request) -> AdminPrincipal:
    token = request.cookies.get(ADMIN_SESSION_COOKIE)
    if not token:
        return _security(request).authenticate(None)

    csrf_token = request.headers.get(ADMIN_CSRF_HEADER)
    if not csrf_token or not _csrf(request).verify(
        session_token=token,
        csrf_token=csrf_token,
    ):
        raise DomainError(
            "ADMIN_CSRF_INVALID",
            "Admin CSRF verification failed",
            403,
        )
    return _security(request).authenticate(token)


AdminPrincipalDep = Annotated[AdminPrincipal, Depends(_admin_principal)]
AdminMutationPrincipalDep = Annotated[
    AdminPrincipal,
    Depends(_admin_state_change_principal),
]
AuthoringDep = Annotated[SecuredContentAuthoringService, Depends(_authoring)]


def _domain_version(
    body: VersionDraftInput,
    *,
    case_id: UUID,
    version_id: UUID,
    version_no: int,
    state: ContentLifecycle,
    created_at: datetime,
    published_at: datetime | None,
) -> AuthoringCaseVersion:
    return AuthoringCaseVersion(
        id=version_id,
        case_id=case_id,
        version_no=version_no,
        state=state,
        title=body.title,
        summary=body.summary,
        base_format_code=body.base_format_code,
        primary_domain_code=body.primary_domain_code,
        content_risk=body.content_risk,
        issues=tuple(
            AuthoringIssue(
                id=issue.id,
                code=issue.code,
                title=issue.title,
                sort_order=issue.sort_order,
                questions=tuple(
                    AuthoringQuestion(
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
                ),
            )
            for issue in body.issues
        ),
        context_blocks=tuple(
            AuthoringContextBlock(
                id=block.id,
                title=block.title,
                body=block.body,
                disclosure_level=block.disclosure_level,
                claim_status=block.claim_status,
                source_ids=tuple(block.source_ids),
                sort_order=block.sort_order,
                block_type=block.block_type,
            )
            for block in body.context_blocks
        ),
        sources=tuple(
            AuthoringSourceReference(
                id=source.id,
                source_kind=source.source_kind,
                locator=source.locator,
                title=source.title,
                publisher=source.publisher,
                published_at=source.published_at,
                claim_status=source.claim_status,
                verified=source.verified,
            )
            for source in body.sources
        ),
        modifiers=tuple(body.modifiers),
        is_fact_bearing=body.is_fact_bearing,
        is_real_event=body.is_real_event,
        required_review_modes=tuple(body.required_review_modes),
        completed_review_modes=tuple(body.completed_review_modes),
        created_at=created_at,
        published_at=published_at,
    )


def _response(version: AuthoringCaseVersion) -> VersionResponse:
    return VersionResponse(
        case_id=version.case_id,
        version_id=version.id,
        version_no=version.version_no,
        state=version.state.value,
        title=version.title,
        published_at=version.published_at,
    )


@router.post("/cases", response_model=VersionResponse, status_code=201)
def create_case(
    body: CreateCaseRequest,
    principal: AdminMutationPrincipalDep,
    authoring: AuthoringDep,
) -> VersionResponse:
    case_id = uuid4()
    identity = CaseIdentity(id=case_id, slug=body.slug)
    version = _domain_version(
        body.version,
        case_id=case_id,
        version_id=uuid4(),
        version_no=1,
        state=ContentLifecycle.DRAFT,
        created_at=identity.created_at,
        published_at=None,
    )
    return _response(
        authoring.create_case(
            principal,
            identity=identity,
            initial_version=version,
        )
    )


@router.post(
    "/case-versions/{version_id}/revisions",
    response_model=VersionResponse,
    status_code=201,
)
def create_revision(
    version_id: UUID,
    principal: AdminMutationPrincipalDep,
    authoring: AuthoringDep,
) -> VersionResponse:
    return _response(
        authoring.create_revision(principal, source_version_id=version_id)
    )


@router.put("/case-versions/{version_id}", response_model=VersionResponse)
def save_draft(
    version_id: UUID,
    body: VersionDraftInput,
    principal: AdminMutationPrincipalDep,
    authoring: AuthoringDep,
) -> VersionResponse:
    current = authoring.version_for_edit(principal, version_id)
    updated = _domain_version(
        body,
        case_id=current.case_id,
        version_id=current.id,
        version_no=current.version_no,
        state=current.state,
        created_at=current.created_at,
        published_at=current.published_at,
    )
    return _response(authoring.save_draft(principal, updated))


@router.post("/case-versions/{version_id}/submit-review", response_model=VersionResponse)
def submit_review(
    version_id: UUID,
    principal: AdminMutationPrincipalDep,
    authoring: AuthoringDep,
) -> VersionResponse:
    return _response(authoring.submit_for_review(principal, version_id))


@router.post("/case-versions/{version_id}/approve", response_model=VersionResponse)
def approve(
    version_id: UUID,
    principal: AdminMutationPrincipalDep,
    authoring: AuthoringDep,
) -> VersionResponse:
    return _response(authoring.approve(principal, version_id))


@router.post("/case-versions/{version_id}/reject", response_model=VersionResponse)
def reject(
    version_id: UUID,
    body: RationaleRequest,
    principal: AdminMutationPrincipalDep,
    authoring: AuthoringDep,
) -> VersionResponse:
    return _response(
        authoring.reject(
            principal,
            version_id,
            rationale=body.rationale,
        )
    )


@router.post("/case-versions/{version_id}/publish", response_model=VersionResponse)
def publish(
    version_id: UUID,
    principal: AdminMutationPrincipalDep,
    authoring: AuthoringDep,
) -> VersionResponse:
    return _response(authoring.publish(principal, version_id))


@router.post("/case-versions/{version_id}/withdraw", response_model=VersionResponse)
def withdraw(
    version_id: UUID,
    body: RationaleRequest,
    principal: AdminMutationPrincipalDep,
    authoring: AuthoringDep,
) -> VersionResponse:
    return _response(
        authoring.withdraw(
            principal,
            version_id,
            rationale=body.rationale,
        )
    )


@router.get("/cases/{case_id}/audit", response_model=AuditTrailResponse)
def audit_trail(
    case_id: UUID,
    principal: AdminPrincipalDep,
    authoring: AuthoringDep,
) -> AuditTrailResponse:
    entries = authoring.audit_trail(principal, case_id)
    return AuditTrailResponse(
        items=[
            AuditEntryResponse(
                audit_id=entry.audit_id,
                case_id=entry.case_id,
                case_version_id=entry.case_version_id,
                actor_ref=entry.actor_ref,
                command=entry.command,
                previous_state=(
                    entry.previous_state.value if entry.previous_state is not None else None
                ),
                new_state=entry.new_state.value,
                rationale=entry.rationale,
                occurred_at=entry.occurred_at,
            )
            for entry in entries
        ]
    )
