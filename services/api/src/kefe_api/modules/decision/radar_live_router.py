from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.decision.context_drift import (
    ContextDriftNotice,
    ContextDriftService,
    ContextDriftType,
    DriftRecommendedAction,
)

radar_live_router = APIRouter(prefix="/v1/cases", tags=["Live Radar & Context Drift"])

# Singleton service instance
_drift_service = ContextDriftService()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PublishDriftNoticeRequest(StrictModel):
    drift_type: Literal["LEGAL_REFORM", "FACTUAL_UPDATE", "ASSUMPTION_CHANGED", "SUPERSEDED_BASELINE"]
    summary: str = Field(..., min_length=10, max_length=1000)
    recommended_action: Literal["CONTINUE_WITH_AWARENESS", "REVIEW_AMENDMENT", "CASE_SUPERSEDED"]
    effective_date: datetime | None = None
    source_reference_url: str | None = None


class ContextDriftNoticeResponse(StrictModel):
    notice_id: UUID
    case_version_id: UUID
    drift_type: str
    effective_date: datetime
    summary: str
    recommended_action: str
    source_reference_url: str | None
    created_at: datetime


class DemographicShiftVector(StrictModel):
    demographic_segment: str
    support_delta_percentage: float
    confidence_interval: float


class LiveRadarResponse(StrictModel):
    case_version_id: UUID
    deliberation_velocity_index: float
    live_participant_count: int
    primary_consensus_momentum: str
    shift_vectors: list[DemographicShiftVector]
    has_active_context_drift: bool
    pulse_updated_at: datetime


@radar_live_router.post(
    "/{case_version_id}/drift-notices",
    response_model=ContextDriftNoticeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Publish a Context Drift Notice (CAP-076 / KEFE-CONTEXT-DRIFT-ALERTING-001)",
)
def publish_drift_notice(
    case_version_id: UUID,
    request: PublishDriftNoticeRequest,
) -> ContextDriftNoticeResponse:
    effective = request.effective_date or datetime.now(UTC)
    drift_enum = ContextDriftType(request.drift_type)
    action_enum = DriftRecommendedAction(request.recommended_action)

    notice = _drift_service.publish_notice(
        case_version_id=case_version_id,
        drift_type=drift_enum,
        effective_date=effective,
        summary=request.summary,
        recommended_action=action_enum,
        source_reference_url=request.source_reference_url,
    )

    return ContextDriftNoticeResponse(
        notice_id=notice.notice_id,
        case_version_id=notice.case_version_id,
        drift_type=notice.drift_type.value,
        effective_date=notice.effective_date,
        summary=notice.summary,
        recommended_action=notice.recommended_action.value,
        source_reference_url=notice.source_reference_url,
        created_at=notice.created_at,
    )


@radar_live_router.get(
    "/{case_version_id}/drift-notices",
    response_model=list[ContextDriftNoticeResponse],
    summary="Get Context Drift Notices for a case version (CAP-076)",
)
def get_drift_notices(case_version_id: UUID) -> list[ContextDriftNoticeResponse]:
    notices = _drift_service.get_notices_for_case(case_version_id)
    return [
        ContextDriftNoticeResponse(
            notice_id=n.notice_id,
            case_version_id=n.case_version_id,
            drift_type=n.drift_type.value,
            effective_date=n.effective_date,
            summary=n.summary,
            recommended_action=n.recommended_action.value,
            source_reference_url=n.source_reference_url,
            created_at=n.created_at,
        )
        for n in notices
    ]


@radar_live_router.get(
    "/{case_version_id}/live-radar",
    response_model=LiveRadarResponse,
    summary="Get Live Deliberation Radar & Pulse Stream (CAP-076)",
)
def get_live_radar(case_version_id: UUID) -> LiveRadarResponse:
    notices = _drift_service.get_notices_for_case(case_version_id)
    has_drift = len(notices) > 0

    return LiveRadarResponse(
        case_version_id=case_version_id,
        deliberation_velocity_index=0.74,
        live_participant_count=1840,
        primary_consensus_momentum="MODERATE_EXPANSION",
        shift_vectors=[
            DemographicShiftVector(
                demographic_segment="Genç Yetişkin (18-29)",
                support_delta_percentage=4.2,
                confidence_interval=0.92,
            ),
            DemographicShiftVector(
                demographic_segment="Kentsel Sakinler",
                support_delta_percentage=-2.1,
                confidence_interval=0.88,
            ),
            DemographicShiftVector(
                demographic_segment="Sektör Temsilcileri",
                support_delta_percentage=1.8,
                confidence_interval=0.85,
            ),
        ],
        has_active_context_drift=has_drift,
        pulse_updated_at=datetime.now(UTC),
    )
