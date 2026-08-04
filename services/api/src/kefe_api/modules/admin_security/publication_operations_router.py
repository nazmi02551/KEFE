from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.case_builder_router import (
    CaseBuilderVersionResponse,
    _version_response,
)
from kefe_api.modules.admin_security.router import (
    AuthoringDep,
    ReadPrincipalDep,
    WritePrincipalDep,
)
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    ContentLifecycle,
    LifecycleAuditEntry,
    PublicationPreflightResult,
    ResolvedFlowDefinition,
)

router = APIRouter(
    prefix="/internal/admin/v1/publication-operations",
    tags=["Internal Admin Publication Operations"],
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PublicationQueueState(StrEnum):
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"


class PublicationQueueItem(StrictModel):
    version_id: UUID
    case_id: UUID
    version_no: int
    state: str
    title: str
    content_risk: str
    primary_domain_code: str
    content_locale: str
    flow_template_code: str
    flow_template_version_no: int
    created_at: datetime
    published_at: datetime | None


class PublicationQueueResponse(StrictModel):
    items: list[PublicationQueueItem]
    next_offset: int | None


class PublicationAuditResponse(StrictModel):
    audit_id: UUID
    actor_ref: str
    command: str
    previous_state: str | None
    new_state: str
    rationale: str | None
    occurred_at: datetime


class PublicationPinResponse(StrictModel):
    content_configuration_id: UUID | None
    content_configuration_version_no: int | None
    flow_template_code: str | None
    flow_template_version_no: int | None
    entry_step_code: str | None


class PublicationDetailResponse(StrictModel):
    version: CaseBuilderVersionResponse
    pin: PublicationPinResponse
    approval: PublicationAuditResponse | None
    publication: PublicationAuditResponse | None


class PublicationValidationFailureResponse(StrictModel):
    code: str
    detail: str
    path: str | None


class PublicationPreflightResponse(StrictModel):
    version_id: UUID
    eligible: bool
    validation_failures: list[PublicationValidationFailureResponse]
    prospective_content_configuration_id: UUID | None
    prospective_content_configuration_version_no: int | None
    prospective_flow_template_code: str | None
    prospective_flow_template_version_no: int | None
    prospective_entry_step_code: str | None
    advisory_only: Literal[True] = True


class PublicationDecisionRequest(StrictModel):
    decision: Literal["PUBLISH", "WITHDRAW"]
    acknowledge_immutable: bool = False
    rationale: str | None = Field(default=None, max_length=5000)


class PublicationDecisionResponse(StrictModel):
    decision: Literal["PUBLISH", "WITHDRAW"]
    version: CaseBuilderVersionResponse
    pin: PublicationPinResponse


@router.get("", response_model=PublicationQueueResponse)
def publication_queue(
    principal: ReadPrincipalDep,
    authoring: AuthoringDep,
    state: PublicationQueueState = PublicationQueueState.APPROVED,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
    content_risk: str | None = Query(default=None, min_length=1, max_length=20),
    primary_domain_code: str | None = Query(
        default=None,
        min_length=1,
        max_length=120,
    ),
) -> PublicationQueueResponse:
    items = authoring.publication_queue(
        principal,
        state=ContentLifecycle(state.value),
        limit=limit,
        offset=offset,
        content_risk=content_risk,
        primary_domain_code=primary_domain_code,
    )
    return PublicationQueueResponse(
        items=[_queue_item(item) for item in items],
        next_offset=offset + limit if len(items) == limit else None,
    )


@router.get("/{version_id}", response_model=PublicationDetailResponse)
def publication_detail(
    version_id: UUID,
    principal: ReadPrincipalDep,
    authoring: AuthoringDep,
) -> PublicationDetailResponse:
    version = authoring.publication_for_inspection(principal, version_id)
    approval, publication = authoring.publication_audit_context(principal, version_id)
    return _detail_response(version, approval=approval, publication=publication)


@router.get("/{version_id}/preflight", response_model=PublicationPreflightResponse)
def publication_preflight(
    version_id: UUID,
    principal: ReadPrincipalDep,
    authoring: AuthoringDep,
) -> PublicationPreflightResponse:
    return _preflight_response(authoring.publication_preflight(principal, version_id))


@router.post("/{version_id}/decision", response_model=PublicationDecisionResponse)
def publication_decision(
    version_id: UUID,
    body: PublicationDecisionRequest,
    principal: WritePrincipalDep,
    authoring: AuthoringDep,
) -> PublicationDecisionResponse:
    if body.decision == "PUBLISH":
        if body.acknowledge_immutable is not True:
            raise DomainError(
                "CONTENT_PUBLICATION_ACK_REQUIRED",
                "Publishing requires explicit immutable-version acknowledgement",
                422,
            )
        if body.rationale is not None and body.rationale.strip():
            raise DomainError(
                "CONTENT_PUBLICATION_DECISION_INVALID",
                "PUBLISH does not accept a withdrawal rationale",
                422,
            )
        version = authoring.publish(principal, version_id)
        return PublicationDecisionResponse(
            decision="PUBLISH",
            version=_version_response(version),
            pin=_pin_response(version),
        )

    if body.acknowledge_immutable:
        raise DomainError(
            "CONTENT_PUBLICATION_DECISION_INVALID",
            "WITHDRAW uses a rationale and does not accept publication acknowledgement",
            422,
        )
    rationale = body.rationale.strip() if body.rationale is not None else ""
    if not rationale:
        raise DomainError(
            "CONTENT_WITHDRAW_RATIONALE_REQUIRED",
            "Withdrawal rationale is required",
            422,
        )
    version = authoring.withdraw(
        principal,
        version_id,
        rationale=rationale,
    )
    return PublicationDecisionResponse(
        decision="WITHDRAW",
        version=_version_response(version),
        pin=_pin_response(version),
    )


def _queue_item(version: AuthoringCaseVersion) -> PublicationQueueItem:
    return PublicationQueueItem(
        version_id=version.id,
        case_id=version.case_id,
        version_no=version.version_no,
        state=version.state.value,
        title=version.title,
        content_risk=version.content_risk,
        primary_domain_code=version.primary_domain_code,
        content_locale=version.content_locale,
        flow_template_code=version.flow_template_code,
        flow_template_version_no=version.flow_template_version_no,
        created_at=version.created_at,
        published_at=version.published_at,
    )


def _detail_response(
    version: AuthoringCaseVersion,
    *,
    approval: LifecycleAuditEntry | None,
    publication: LifecycleAuditEntry | None,
) -> PublicationDetailResponse:
    return PublicationDetailResponse(
        version=_version_response(version),
        pin=_pin_response(version),
        approval=_audit_response(approval) if approval is not None else None,
        publication=_audit_response(publication) if publication is not None else None,
    )


def _pin_response(version: AuthoringCaseVersion) -> PublicationPinResponse:
    flow = version.resolved_flow
    return PublicationPinResponse(
        content_configuration_id=version.content_configuration_id,
        content_configuration_version_no=version.content_configuration_version_no,
        flow_template_code=flow.template_code if flow is not None else None,
        flow_template_version_no=flow.template_version_no if flow is not None else None,
        entry_step_code=flow.entry_step_code if flow is not None else None,
    )


def _preflight_response(
    result: PublicationPreflightResult,
) -> PublicationPreflightResponse:
    resolution = result.resolution
    flow: ResolvedFlowDefinition | None = (
        resolution.resolved_flow if resolution is not None else None
    )
    return PublicationPreflightResponse(
        version_id=result.version_id,
        eligible=result.eligible,
        validation_failures=[
            PublicationValidationFailureResponse(
                code=item.code,
                detail=item.detail,
                path=item.path,
            )
            for item in result.validation_failures[:100]
        ],
        prospective_content_configuration_id=(
            resolution.content_configuration_id if resolution is not None else None
        ),
        prospective_content_configuration_version_no=(
            resolution.content_configuration_version_no if resolution is not None else None
        ),
        prospective_flow_template_code=flow.template_code if flow is not None else None,
        prospective_flow_template_version_no=(
            flow.template_version_no if flow is not None else None
        ),
        prospective_entry_step_code=flow.entry_step_code if flow is not None else None,
    )


def _audit_response(entry: LifecycleAuditEntry) -> PublicationAuditResponse:
    return PublicationAuditResponse(
        audit_id=entry.audit_id,
        actor_ref=entry.actor_ref,
        command=entry.command,
        previous_state=entry.previous_state.value if entry.previous_state else None,
        new_state=entry.new_state.value,
        rationale=entry.rationale,
        occurred_at=entry.occurred_at,
    )
