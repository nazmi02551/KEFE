from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, ConfigDict

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_operational_reports.models import (
    AdminOperationalReportSnapshot,
)
from kefe_api.modules.admin_security.operational_reports import (
    SecuredAdminOperationalReportsService,
)
from kefe_api.modules.admin_security.router import ReadPrincipalDep, WritePrincipalDep
from kefe_api.modules.identity.otp_delivery_health import OtpDeliveryAlertRecord

router = APIRouter(
    prefix="/internal/admin/v1/operational-reports",
    tags=["Internal Admin Operational Reports"],
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OperationalThresholdsResponse(StrictModel):
    in_review_attention_threshold: int
    pending_proposal_attention_threshold: int
    moderation_candidate_attention_threshold: int


class ContentSupplyPolicyResponse(StrictModel):
    pending_dispatch_attention_threshold: int
    queued_run_attention_threshold: int
    unreviewed_proposal_attention_threshold: int
    recent_non_success_attention_threshold: int
    max_cycle_silence_seconds: int
    failure_window_seconds: int


class ContentSupplySnapshotResponse(StrictModel):
    signal: str
    as_of: datetime
    reason_codes: list[str]
    active_schedule_count: int
    paused_schedule_count: int
    due_schedule_count: int
    pending_dispatch_count: int
    running_dispatch_count: int
    stale_dispatch_count: int
    recent_dispatch_non_success_count: int
    queued_ingestion_run_count: int
    running_ingestion_run_count: int
    stale_ingestion_lease_count: int
    recent_failed_ingestion_run_count: int
    unreviewed_proposal_count: int
    running_cycle_count: int
    stale_cycle_count: int
    recent_non_success_cycle_count: int
    latest_terminal_cycle_state: str | None
    latest_terminal_cycle_completed_at: datetime | None
    seconds_since_latest_terminal_cycle: int | None


class OperationalReportsSnapshotResponse(StrictModel):
    as_of: datetime
    overall_signal: str
    reason_codes: list[str]
    thresholds: OperationalThresholdsResponse
    content_supply_policy: ContentSupplyPolicyResponse
    content_supply: ContentSupplySnapshotResponse
    editorial_lifecycle: dict[str, int]
    proposal_review: dict[str, int]
    moderation: dict[str, int]
    aggregate_only: bool = True


class OtpDeliveryAlertCandidateResponse(StrictModel):
    candidate_id: UUID
    signal: str
    reason_codes: list[str]
    observed_at: datetime
    window_started_at: datetime
    total_count: int
    accepted_count: int
    unavailable_count: int
    rejected_count: int
    failure_ratio_bps: int | None
    created_at: datetime
    acknowledged: bool
    acknowledged_at: datetime | None
    acknowledged_by_actor_ref: str | None
    acknowledgement_is_resolution: bool = False


class OtpDeliveryAlertCandidateListResponse(StrictModel):
    items: list[OtpDeliveryAlertCandidateResponse]
    aggregate_only: bool = True
    acknowledgement_is_resolution: bool = False


class OtpDeliveryAlertAcknowledgementRequest(StrictModel):
    expected_candidate_id: UUID
    acknowledgement: Literal["ACKNOWLEDGE"]


def get_reports(request: Request) -> SecuredAdminOperationalReportsService:
    return request.app.state.secured_admin_operational_reports_service


ReportsDep = Annotated[
    SecuredAdminOperationalReportsService,
    Depends(get_reports),
]


@router.get("/snapshot", response_model=OperationalReportsSnapshotResponse)
def operational_reports_snapshot(
    principal: ReadPrincipalDep,
    reports: ReportsDep,
) -> OperationalReportsSnapshotResponse:
    return _response(reports.snapshot(principal))


@router.get(
    "/otp-delivery-alerts",
    response_model=OtpDeliveryAlertCandidateListResponse,
)
def otp_delivery_alert_candidates(
    principal: ReadPrincipalDep,
    reports: ReportsDep,
    acknowledged: bool | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10_000),
) -> OtpDeliveryAlertCandidateListResponse:
    records = reports.otp_delivery_alert_candidates(
        principal,
        acknowledged=acknowledged,
        limit=limit,
        offset=offset,
    )
    return OtpDeliveryAlertCandidateListResponse(
        items=[_alert_response(record) for record in records]
    )


@router.post(
    "/otp-delivery-alerts/{candidate_id}/acknowledgement",
    response_model=OtpDeliveryAlertCandidateResponse,
)
def acknowledge_otp_delivery_alert(
    candidate_id: UUID,
    body: OtpDeliveryAlertAcknowledgementRequest,
    principal: WritePrincipalDep,
    reports: ReportsDep,
) -> OtpDeliveryAlertCandidateResponse:
    if body.expected_candidate_id != candidate_id:
        raise DomainError(
            "ADMIN_OPERATIONAL_ALERT_ACK_MISMATCH",
            "OTP delivery alert acknowledgement does not match the selected candidate",
            409,
        )
    return _alert_response(
        reports.acknowledge_otp_delivery_alert(
            principal,
            candidate_id=candidate_id,
        )
    )


def _response(
    snapshot: AdminOperationalReportSnapshot,
) -> OperationalReportsSnapshotResponse:
    supply = snapshot.content_supply
    policy = snapshot.policy
    supply_policy = policy.content_supply
    return OperationalReportsSnapshotResponse(
        as_of=snapshot.as_of,
        overall_signal=snapshot.overall_signal.value,
        reason_codes=list(snapshot.reason_codes),
        thresholds=OperationalThresholdsResponse(
            in_review_attention_threshold=policy.in_review_attention_threshold,
            pending_proposal_attention_threshold=(policy.pending_proposal_attention_threshold),
            moderation_candidate_attention_threshold=(
                policy.moderation_candidate_attention_threshold
            ),
        ),
        content_supply_policy=ContentSupplyPolicyResponse(
            pending_dispatch_attention_threshold=(
                supply_policy.pending_dispatch_attention_threshold
            ),
            queued_run_attention_threshold=(supply_policy.queued_run_attention_threshold),
            unreviewed_proposal_attention_threshold=(
                supply_policy.unreviewed_proposal_attention_threshold
            ),
            recent_non_success_attention_threshold=(
                supply_policy.recent_non_success_attention_threshold
            ),
            max_cycle_silence_seconds=supply_policy.max_cycle_silence_seconds,
            failure_window_seconds=supply_policy.failure_window_seconds,
        ),
        content_supply=ContentSupplySnapshotResponse(
            signal=supply.signal.value,
            as_of=supply.as_of,
            reason_codes=list(supply.reason_codes),
            active_schedule_count=supply.active_schedule_count,
            paused_schedule_count=supply.paused_schedule_count,
            due_schedule_count=supply.due_schedule_count,
            pending_dispatch_count=supply.pending_dispatch_count,
            running_dispatch_count=supply.running_dispatch_count,
            stale_dispatch_count=supply.stale_dispatch_count,
            recent_dispatch_non_success_count=(supply.recent_dispatch_non_success_count),
            queued_ingestion_run_count=supply.queued_ingestion_run_count,
            running_ingestion_run_count=supply.running_ingestion_run_count,
            stale_ingestion_lease_count=supply.stale_ingestion_lease_count,
            recent_failed_ingestion_run_count=(supply.recent_failed_ingestion_run_count),
            unreviewed_proposal_count=supply.unreviewed_proposal_count,
            running_cycle_count=supply.running_cycle_count,
            stale_cycle_count=supply.stale_cycle_count,
            recent_non_success_cycle_count=(supply.recent_non_success_cycle_count),
            latest_terminal_cycle_state=supply.latest_terminal_cycle_state,
            latest_terminal_cycle_completed_at=(supply.latest_terminal_cycle_completed_at),
            seconds_since_latest_terminal_cycle=(supply.seconds_since_latest_terminal_cycle),
        ),
        editorial_lifecycle=dict(snapshot.editorial_lifecycle),
        proposal_review=dict(snapshot.proposal_review),
        moderation=dict(snapshot.moderation),
    )


def _alert_response(record: OtpDeliveryAlertRecord) -> OtpDeliveryAlertCandidateResponse:
    candidate = record.candidate
    acknowledgement = record.acknowledgement
    return OtpDeliveryAlertCandidateResponse(
        candidate_id=candidate.id,
        signal=candidate.signal.value,
        reason_codes=list(candidate.reason_codes),
        observed_at=candidate.observed_at,
        window_started_at=candidate.window_started_at,
        total_count=candidate.total_count,
        accepted_count=candidate.accepted_count,
        unavailable_count=candidate.unavailable_count,
        rejected_count=candidate.rejected_count,
        failure_ratio_bps=candidate.failure_ratio_bps,
        created_at=candidate.created_at,
        acknowledged=record.acknowledged,
        acknowledged_at=(
            acknowledgement.acknowledged_at if acknowledgement is not None else None
        ),
        acknowledged_by_actor_ref=(
            acknowledgement.actor_ref if acknowledgement is not None else None
        ),
    )
