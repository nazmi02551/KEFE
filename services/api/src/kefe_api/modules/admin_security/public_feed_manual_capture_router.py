from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request

from kefe_api.modules.admin_security.router import (
    ReadPrincipalDep,
    StrictModel,
    WritePrincipalDep,
)
from kefe_api.modules.knowledge.public_feed_manual_capture import (
    ApprovedPublicFeedManualCaptureService,
    PublicFeedManualCaptureAuditEntry,
    PublicFeedManualCaptureExecutionResult,
)

router = APIRouter(
    prefix="/internal/admin/v1/public-feeds",
    tags=["Internal Admin Public Feed Capture"],
)


class PublicFeedManualCaptureResponse(StrictModel):
    execution_id: UUID
    catalog_entry_id: UUID
    feed_code: str
    configuration_hash: str
    trace_id: str
    outcome: str
    source_artifact_id: UUID | None
    ingestion_run_id: UUID | None
    duration_ms: int
    error_code: str | None


class PublicFeedManualCaptureAuditResponse(StrictModel):
    event_id: UUID
    execution_id: UUID
    catalog_entry_id: UUID
    feed_code: str
    configuration_hash: str
    actor_ref: str
    trace_id: str
    outcome: str
    source_artifact_id: UUID | None
    ingestion_run_id: UUID | None
    duration_ms: int
    error_code: str | None
    occurred_at: datetime


class PublicFeedManualCaptureAuditListResponse(StrictModel):
    items: list[PublicFeedManualCaptureAuditResponse]


def get_manual_capture_service(
    request: Request,
) -> ApprovedPublicFeedManualCaptureService:
    return request.app.state.public_feed_manual_capture_service


ManualCaptureDep = Annotated[
    ApprovedPublicFeedManualCaptureService,
    Depends(get_manual_capture_service),
]


@router.get(
    "/capture-audit",
    response_model=PublicFeedManualCaptureAuditListResponse,
)
def list_manual_capture_audit(
    principal: ReadPrincipalDep,
    service: ManualCaptureDep,
) -> PublicFeedManualCaptureAuditListResponse:
    return PublicFeedManualCaptureAuditListResponse(
        items=[_audit_response(item) for item in service.list_audit(principal)]
    )


@router.get(
    "/{entry_id}/capture-audit",
    response_model=PublicFeedManualCaptureAuditListResponse,
)
def public_feed_manual_capture_audit(
    entry_id: UUID,
    principal: ReadPrincipalDep,
    service: ManualCaptureDep,
) -> PublicFeedManualCaptureAuditListResponse:
    return PublicFeedManualCaptureAuditListResponse(
        items=[
            _audit_response(item)
            for item in service.list_audit(principal, entry_id)
        ]
    )


@router.post(
    "/{entry_id}/capture-once",
    response_model=PublicFeedManualCaptureResponse,
)
def capture_public_feed_once(
    entry_id: UUID,
    principal: WritePrincipalDep,
    service: ManualCaptureDep,
    trace_id: Annotated[
        str | None,
        Header(alias="X-KEFE-Trace-ID", max_length=128),
    ] = None,
) -> PublicFeedManualCaptureResponse:
    return _result_response(
        service.capture_once(
            principal,
            catalog_entry_id=entry_id,
            trace_id=trace_id,
        )
    )


def _result_response(
    result: PublicFeedManualCaptureExecutionResult,
) -> PublicFeedManualCaptureResponse:
    return PublicFeedManualCaptureResponse(
        execution_id=result.execution_id,
        catalog_entry_id=result.catalog_entry_id,
        feed_code=result.feed_code,
        configuration_hash=result.configuration_hash,
        trace_id=result.trace_id,
        outcome=result.outcome.value,
        source_artifact_id=result.source_artifact_id,
        ingestion_run_id=result.ingestion_run_id,
        duration_ms=result.duration_ms,
        error_code=result.error_code,
    )


def _audit_response(
    entry: PublicFeedManualCaptureAuditEntry,
) -> PublicFeedManualCaptureAuditResponse:
    return PublicFeedManualCaptureAuditResponse(
        event_id=entry.event_id,
        execution_id=entry.execution_id,
        catalog_entry_id=entry.catalog_entry_id,
        feed_code=entry.feed_code,
        configuration_hash=entry.configuration_hash,
        actor_ref=entry.actor_ref,
        trace_id=entry.trace_id,
        outcome=entry.outcome,
        source_artifact_id=entry.source_artifact_id,
        ingestion_run_id=entry.ingestion_run_id,
        duration_ms=entry.duration_ms,
        error_code=entry.error_code,
        occurred_at=entry.occurred_at,
    )
