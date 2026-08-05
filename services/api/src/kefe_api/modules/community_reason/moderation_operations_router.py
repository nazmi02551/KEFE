from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.router import ReadPrincipalDep, WritePrincipalDep
from kefe_api.modules.community_reason.models import (
    CommunityReasonModeration,
    CommunityReasonModerationAudit,
    CommunityReasonModerationItem,
    CommunityReasonModerationQueueKind,
    ReasonReportCode,
)
from kefe_api.modules.community_reason.service import CommunityReasonService

router = APIRouter(
    prefix="/community-reason-moderation",
    tags=["Internal Admin Community Reason Moderation"],
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ReasonModerationItemResponse(StrictModel):
    reason_id: UUID
    case_version_id: UUID
    tags: list[str]
    body: str | None
    moderation_state: str
    created_at: datetime
    updated_at: datetime
    report_count: int
    report_counts_by_code: dict[str, int]
    latest_reported_at: datetime | None
    candidate_at: datetime


class ReasonModerationQueueResponse(StrictModel):
    items: list[ReasonModerationItemResponse]
    next_offset: int | None


class ReasonModerationAuditResponse(StrictModel):
    audit_id: UUID
    reason_id: UUID
    actor_ref: str
    previous_state: str
    decided_state: str
    rationale: str
    created_at: datetime


class ReasonModerationAuditTrailResponse(StrictModel):
    items: list[ReasonModerationAuditResponse]


class ReasonModerationDecisionRequest(StrictModel):
    state: Literal["ALLOWED", "BLOCKED"]
    rationale: str = Field(min_length=10, max_length=1000)
    confirm_reason_id: UUID


class ReasonModerationDecisionResponse(StrictModel):
    reason: ReasonModerationItemResponse
    audit: ReasonModerationAuditResponse


def get_service(request: Request) -> CommunityReasonService:
    return request.app.state.community_reason_service


ServiceDep = Annotated[CommunityReasonService, Depends(get_service)]


@router.get("", response_model=ReasonModerationQueueResponse)
def moderation_queue(
    request: Request,
    principal: ReadPrincipalDep,
    service: ServiceDep,
    kind: CommunityReasonModerationQueueKind = CommunityReasonModerationQueueKind.PENDING,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    case_version_id: UUID | None = None,
    report_code: ReasonReportCode | None = None,
) -> ReasonModerationQueueResponse:
    _authorize(request, principal, AdminCapability.CONTENT_MODERATE)
    items = service.moderation_queue(
        kind=kind,
        limit=limit,
        offset=offset,
        case_version_id=case_version_id,
        report_code=report_code,
    )
    return ReasonModerationQueueResponse(
        items=[_item_response(item) for item in items],
        next_offset=offset + limit if len(items) == limit else None,
    )


@router.get("/{reason_id}", response_model=ReasonModerationItemResponse)
def moderation_detail(
    reason_id: UUID,
    request: Request,
    principal: ReadPrincipalDep,
    service: ServiceDep,
) -> ReasonModerationItemResponse:
    _authorize(request, principal, AdminCapability.CONTENT_MODERATE)
    return _item_response(service.moderation_inspection(reason_id=reason_id))


@router.get(
    "/{reason_id}/audit",
    response_model=ReasonModerationAuditTrailResponse,
)
def moderation_audit(
    reason_id: UUID,
    request: Request,
    principal: ReadPrincipalDep,
    service: ServiceDep,
    limit: int = Query(default=100, ge=1, le=100),
) -> ReasonModerationAuditTrailResponse:
    _authorize(request, principal, AdminCapability.AUDIT_READ)
    audits = service.moderation_audit(reason_id=reason_id, limit=limit)
    return ReasonModerationAuditTrailResponse(
        items=[_audit_response(audit) for audit in audits]
    )


@router.post(
    "/{reason_id}/decision",
    response_model=ReasonModerationDecisionResponse,
)
def moderation_decision(
    reason_id: UUID,
    body: ReasonModerationDecisionRequest,
    request: Request,
    principal: WritePrincipalDep,
    service: ServiceDep,
) -> ReasonModerationDecisionResponse:
    _authorize(request, principal, AdminCapability.CONTENT_MODERATE)
    if body.confirm_reason_id != reason_id:
        raise DomainError(
            "COMMUNITY_REASON_MODERATION_CONFIRMATION_INVALID",
            "Moderation confirmation must match the selected reason",
            422,
        )
    decision = service.moderate(
        reason_id=reason_id,
        state=CommunityReasonModeration(body.state),
        actor_ref=principal.audit_actor_ref,
        rationale=body.rationale,
    )
    detail = service.moderation_inspection(reason_id=reason_id)
    return ReasonModerationDecisionResponse(
        reason=_item_response(detail),
        audit=_audit_response(decision.audit),
    )


def _authorize(
    request: Request,
    principal: AdminPrincipal,
    capability: AdminCapability,
) -> None:
    request.app.state.admin_security_service.authorize(principal, capability)


def _item_response(item: CommunityReasonModerationItem) -> ReasonModerationItemResponse:
    return ReasonModerationItemResponse(
        reason_id=item.reason_id,
        case_version_id=item.case_version_id,
        tags=list(item.tags),
        body=item.body,
        moderation_state=item.moderation_state.value,
        created_at=item.created_at,
        updated_at=item.updated_at,
        report_count=item.report_count,
        report_counts_by_code=dict(item.report_counts_by_code),
        latest_reported_at=item.latest_reported_at,
        candidate_at=item.candidate_at,
    )


def _audit_response(
    audit: CommunityReasonModerationAudit,
) -> ReasonModerationAuditResponse:
    return ReasonModerationAuditResponse(
        audit_id=audit.audit_id,
        reason_id=audit.reason_id,
        actor_ref=audit.actor_ref,
        previous_state=audit.previous_state.value,
        decided_state=audit.decided_state.value,
        rationale=audit.rationale,
        created_at=audit.created_at,
    )
