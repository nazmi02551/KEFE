from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from kefe_api.modules.decision.dynamic_agenda_thresholding import (
    DynamicAgendaResult,
    DynamicAgendaThresholdingService,
)
from kefe_api.modules.decision.synthetic_astroturfing_shield import (
    BotDefenseState,
    BotShieldResult,
    SyntheticAstroturfingShieldService,
)

trust_integrity_router = APIRouter(prefix="/v1/trust", tags=["Trust & Integrity"])


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClusterInspectionRequest(StrictModel):
    cluster_id: str = Field(..., min_length=2, max_length=128)
    target_case_id: str = Field(..., min_length=2, max_length=128)
    synthetic_probability_score: float = Field(..., ge=0.0, le=1.0)
    quarantined_bot_payloads_count: int = Field(..., ge=0)
    semantic_entropy_index: float = Field(..., ge=0.0, le=1.0)


class ClusterInspectionResponse(StrictModel):
    cluster_id: str
    target_case_id: str
    defense_state: str
    synthetic_probability_score: float
    quarantined_bot_payloads_count: int
    semantic_entropy_index: float
    is_quarantined: bool
    inspected_at: datetime


class AgendaThresholdEvaluationRequest(StrictModel):
    topic_id: str = Field(..., min_length=4, max_length=128)
    topic_title: str = Field(..., min_length=5, max_length=256)
    resonance_velocity_index: float = Field(..., ge=0.0, le=1.0)
    viewpoint_diversity_entropy: float = Field(..., ge=0.0, le=1.0)


class AgendaThresholdEvaluationResponse(StrictModel):
    topic_id: str
    topic_title: str
    priority_tier: str
    resonance_velocity_index: float
    viewpoint_diversity_entropy: float
    is_featured_on_national_ballot: bool
    evaluated_at: datetime


class QuarantineClusterRecord(StrictModel):
    cluster_id: str
    target_case_id: str
    defense_state: str
    synthetic_probability_score: float
    quarantined_bot_payloads_count: int
    semantic_entropy_index: float
    quarantine_status: Literal["ACTIVE", "RESOLVED", "WHITELISTED"]
    updated_at: datetime


# In-memory storage for quarantined clusters
_CLUSTERS_REGISTRY: dict[str, QuarantineClusterRecord] = {
    "bot_cls_001": QuarantineClusterRecord(
        cluster_id="bot_cls_001",
        target_case_id="case_ai_001",
        defense_state=BotDefenseState.ISOLATED_QUARANTINE_SWARM.value,
        synthetic_probability_score=0.94,
        quarantined_bot_payloads_count=1450,
        semantic_entropy_index=0.12,
        quarantine_status="ACTIVE",
        updated_at=datetime(2026, 9, 12, 12, 0, 0, tzinfo=UTC),
    ),
    "bot_cls_002": QuarantineClusterRecord(
        cluster_id="bot_cls_002",
        target_case_id="case_edu_002",
        defense_state=BotDefenseState.SUSPECTED_BOT_COORDINATION.value,
        synthetic_probability_score=0.65,
        quarantined_bot_payloads_count=180,
        semantic_entropy_index=0.38,
        quarantine_status="ACTIVE",
        updated_at=datetime(2026, 9, 12, 15, 30, 0, tzinfo=UTC),
    ),
}


@trust_integrity_router.post(
    "/shield/inspect",
    response_model=ClusterInspectionResponse,
    summary="Inspect bot cluster (CAP-073)",
)
def inspect_cluster(request: ClusterInspectionRequest) -> ClusterInspectionResponse:
    try:
        result = SyntheticAstroturfingShieldService.inspect_cluster(
            cluster_id=request.cluster_id,
            target_case_id=request.target_case_id,
            synthetic_probability_score=request.synthetic_probability_score,
            quarantined_bot_payloads_count=request.quarantined_bot_payloads_count,
            semantic_entropy_index=request.semantic_entropy_index,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    is_quarantined = result.defense_state == BotDefenseState.ISOLATED_QUARANTINE_SWARM

    # Auto-register if quarantined
    if is_quarantined:
        _CLUSTERS_REGISTRY[result.cluster_id] = QuarantineClusterRecord(
            cluster_id=result.cluster_id,
            target_case_id=result.target_case_id,
            defense_state=result.defense_state.value,
            synthetic_probability_score=result.synthetic_probability_score,
            quarantined_bot_payloads_count=result.quarantined_bot_payloads_count,
            semantic_entropy_index=result.semantic_entropy_index,
            quarantine_status="ACTIVE",
            updated_at=datetime.now(UTC),
        )

    return ClusterInspectionResponse(
        cluster_id=result.cluster_id,
        target_case_id=result.target_case_id,
        defense_state=result.defense_state.value,
        synthetic_probability_score=result.synthetic_probability_score,
        quarantined_bot_payloads_count=result.quarantined_bot_payloads_count,
        semantic_entropy_index=result.semantic_entropy_index,
        is_quarantined=is_quarantined,
        inspected_at=datetime.now(UTC),
    )


@trust_integrity_router.post(
    "/agenda/evaluate",
    response_model=AgendaThresholdEvaluationResponse,
    summary="Evaluate dynamic agenda thresholding (CAP-073)",
)
def evaluate_agenda_threshold(
    request: AgendaThresholdEvaluationRequest,
) -> AgendaThresholdEvaluationResponse:
    try:
        result = DynamicAgendaThresholdingService.evaluate_topic(
            topic_id=request.topic_id,
            topic_title=request.topic_title,
            resonance_velocity_index=request.resonance_velocity_index,
            viewpoint_diversity_entropy=request.viewpoint_diversity_entropy,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return AgendaThresholdEvaluationResponse(
        topic_id=result.topic_id,
        topic_title=result.topic_title,
        priority_tier=result.priority_tier.value,
        resonance_velocity_index=result.resonance_velocity_index,
        viewpoint_diversity_entropy=result.viewpoint_diversity_entropy,
        is_featured_on_national_ballot=result.is_featured_on_national_ballot,
        evaluated_at=datetime.now(UTC),
    )


@trust_integrity_router.get(
    "/clusters",
    response_model=list[QuarantineClusterRecord],
    summary="List quarantined and monitored bot clusters (CAP-073)",
)
def list_clusters() -> list[QuarantineClusterRecord]:
    return list(_CLUSTERS_REGISTRY.values())


@trust_integrity_router.post(
    "/clusters/{cluster_id}/status",
    response_model=QuarantineClusterRecord,
    summary="Update quarantine status of a cluster",
)
def update_cluster_status(
    cluster_id: str,
    new_status: Literal["ACTIVE", "RESOLVED", "WHITELISTED"],
) -> QuarantineClusterRecord:
    cluster = _CLUSTERS_REGISTRY.get(cluster_id)
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster {cluster_id} not found",
        )

    updated = QuarantineClusterRecord(
        cluster_id=cluster.cluster_id,
        target_case_id=cluster.target_case_id,
        defense_state=cluster.defense_state,
        synthetic_probability_score=cluster.synthetic_probability_score,
        quarantined_bot_payloads_count=cluster.quarantined_bot_payloads_count,
        semantic_entropy_index=cluster.semantic_entropy_index,
        quarantine_status=new_status,
        updated_at=datetime.now(UTC),
    )
    _CLUSTERS_REGISTRY[cluster_id] = updated
    return updated
