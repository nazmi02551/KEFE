from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.analytics.models import (
    ActivationFunnelMetric,
    ActivationJourney,
    FunnelStageMetric,
    MeaningfulWeighMetric,
    PerspectiveResilienceMetric,
    QualityJourney,
)
from kefe_api.modules.analytics.service import (
    ActivationFunnelCalculator,
    MeaningfulWeighsAggregator,
    PerspectiveResilienceCalculator,
)
from kefe_api.modules.decision.depolarization_index import (
    BridgeEfficacyState,
    DepolarizationCalculator,
    DepolarizationIndexResult,
)

analytics_router = APIRouter(prefix="/v1/analytics", tags=["Analytics & Metrics"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class NorthStarResponse(StrictModel):
    window_start: datetime
    window_end: datetime
    meaningful_weigh_count: int
    weekly_active_weighers: int
    distinct_cases_weighed: int


class FunnelStageItem(StrictModel):
    stage_name: str
    stage_count: int
    conversion_from_start_rate: float
    drop_off_from_previous_rate: float


class ActivationFunnelResponse(StrictModel):
    window_start: datetime
    window_end: datetime
    total_sessions: int
    stages: list[FunnelStageItem]


class QualityResilienceResponse(StrictModel):
    window_start: datetime
    window_end: datetime
    total_exposed_sessions: int
    stable_decisions_count: int
    shifted_decisions_count: int
    resilience_index: float
    attitude_shift_rate: float


class DepolarizationEvaluationRequest(StrictModel):
    case_version_id: UUID
    pre_deliberation_distance: float = Field(..., ge=0.0, le=1.0)
    post_deliberation_distance: float = Field(..., ge=0.0, le=1.0)


class DepolarizationEvaluationResponse(StrictModel):
    case_version_id: UUID
    pre_deliberation_distance: float
    post_deliberation_distance: float
    depolarization_score: float
    bridge_efficacy_state: str
    evaluated_at: datetime


# Synthetic seed journeys for demonstration and local preview
def _get_sample_journeys(now: datetime) -> tuple[list[ActivationJourney], list[QualityJourney]]:
    actors = [uuid4() for _ in range(25)]
    cases = [uuid4() for _ in range(5)]

    act_journeys: list[ActivationJourney] = []
    qual_journeys: list[QualityJourney] = []

    for i in range(50):
        s_id = uuid4()
        actor = actors[i % len(actors)]
        case = cases[i % len(cases)]
        started = now - timedelta(days=i % 6, hours=i)
        committed = started + timedelta(minutes=4) if i < 42 else None
        revealed = committed + timedelta(minutes=1) if committed and i < 38 else None

        act_journeys.append(
            ActivationJourney(
                session_id=s_id,
                actor_id=actor,
                case_version_id=case,
                started_at=started,
                started_source_event_id=uuid4(),
                committed_at=committed,
                committed_source_event_id=uuid4() if committed else None,
                result_revealed_at=revealed,
                result_revealed_source_event_id=uuid4() if revealed else None,
            )
        )

        # Quality journey
        p_viewed = revealed + timedelta(minutes=2) if revealed and i < 30 else None
        revised = p_viewed + timedelta(minutes=3) if p_viewed and i % 3 == 0 else None

        qual_journeys.append(
            QualityJourney(
                session_id=s_id,
                case_version_id=case,
                committed_at=committed,
                committed_source_event_id=uuid4() if committed else None,
                perspective_viewed_at=p_viewed,
                perspective_viewed_source_event_id=uuid4() if p_viewed else None,
                exposure_recorded_at=p_viewed,
                exposure_recorded_source_event_id=uuid4() if p_viewed else None,
                intervention_exposed_at=p_viewed,
                intervention_exposed_source_event_id=uuid4() if p_viewed else None,
                decision_revised_at=revised,
                decision_revised_source_event_id=uuid4() if revised else None,
            )
        )

    return act_journeys, qual_journeys


@analytics_router.get(
    "/north-star",
    response_model=NorthStarResponse,
    summary="Get Meaningful Weighs / WAU Metric (CAP-114)",
)
def get_north_star(window_days: int = Query(7, ge=1, le=90)) -> NorthStarResponse:
    now = datetime.now(UTC)
    window_start = now - timedelta(days=window_days)
    act_journeys, _ = _get_sample_journeys(now)

    metric = MeaningfulWeighsAggregator.calculate(
        act_journeys,
        window_start=window_start,
        window_end=now,
    )

    return NorthStarResponse(
        window_start=metric.window_start,
        window_end=metric.window_end,
        meaningful_weigh_count=metric.meaningful_weigh_count,
        weekly_active_weighers=metric.weekly_active_weighers,
        distinct_cases_weighed=metric.distinct_cases_weighed,
    )


@analytics_router.get(
    "/funnel",
    response_model=ActivationFunnelResponse,
    summary="Get Activation Funnel Metrics (CAP-115)",
)
def get_activation_funnel(window_days: int = Query(7, ge=1, le=90)) -> ActivationFunnelResponse:
    now = datetime.now(UTC)
    window_start = now - timedelta(days=window_days)
    act_journeys, qual_journeys = _get_sample_journeys(now)

    metric = ActivationFunnelCalculator.calculate(
        activation_journeys=act_journeys,
        quality_journeys=qual_journeys,
        window_start=window_start,
        window_end=now,
    )

    stages = [
        FunnelStageItem(
            stage_name=s.stage_name,
            stage_count=s.stage_count,
            conversion_from_start_rate=s.conversion_from_start_rate,
            drop_off_from_previous_rate=s.drop_off_from_previous_rate,
        )
        for s in metric.stages
    ]

    return ActivationFunnelResponse(
        window_start=metric.window_start,
        window_end=metric.window_end,
        total_sessions=metric.total_sessions,
        stages=stages,
    )


@analytics_router.get(
    "/quality",
    response_model=QualityResilienceResponse,
    summary="Get Perspective Resilience and Quality Metrics (CAP-116)",
)
def get_quality_metrics(window_days: int = Query(7, ge=1, le=90)) -> QualityResilienceResponse:
    now = datetime.now(UTC)
    window_start = now - timedelta(days=window_days)
    _, qual_journeys = _get_sample_journeys(now)

    metric = PerspectiveResilienceCalculator.calculate(
        quality_journeys=qual_journeys,
        window_start=window_start,
        window_end=now,
    )

    return QualityResilienceResponse(
        window_start=metric.window_start,
        window_end=metric.window_end,
        total_exposed_sessions=metric.total_exposed_sessions,
        stable_decisions_count=metric.stable_decisions_count,
        shifted_decisions_count=metric.shifted_decisions_count,
        resilience_index=metric.resilience_index,
        attitude_shift_rate=metric.attitude_shift_rate,
    )


@analytics_router.post(
    "/depolarization/evaluate",
    response_model=DepolarizationEvaluationResponse,
    summary="Evaluate Depolarization & Bridge Efficacy Index (CAP-117)",
)
def evaluate_depolarization(
    request: DepolarizationEvaluationRequest,
) -> DepolarizationEvaluationResponse:
    try:
        res = DepolarizationCalculator.calculate(
            case_version_id=request.case_version_id,
            pre_deliberation_distance=request.pre_deliberation_distance,
            post_deliberation_distance=request.post_deliberation_distance,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return DepolarizationEvaluationResponse(
        case_version_id=res.case_version_id,
        pre_deliberation_distance=res.pre_deliberation_distance,
        post_deliberation_distance=res.post_deliberation_distance,
        depolarization_score=res.depolarization_score,
        bridge_efficacy_state=res.bridge_efficacy_state.value,
        evaluated_at=datetime.now(UTC),
    )
