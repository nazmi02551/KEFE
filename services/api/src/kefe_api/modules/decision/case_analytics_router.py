from __future__ import annotations

import json
from datetime import UTC, datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from kefe_api.modules.decision.case_objection import (
    CaseObjectionItem,
    CaseObjectionService,
    ObjectionCategory,
    ObjectionStatus,
)
from kefe_api.modules.decision.case_quality_checklist import (
    CaseQualityChecklistEvaluator,
)
from kefe_api.modules.decision.clustering_models import PerspectiveArchetype
from kefe_api.modules.decision.clustering_service import (
    MultiPartyPerspectiveClusteringService,
)
from kefe_api.modules.decision.correction_history import (
    CaseCorrectionHistoryService,
    CorrectionSeverity,
    CorrectionType,
)
from kefe_api.modules.decision.divergence_classifier import (
    ConsensusDivergenceClassifier,
    DivergenceClassification,
)
from kefe_api.modules.decision.expert_public_gap import ExpertPublicGapService
from kefe_api.modules.decision.incentive_map import IncentiveMapCalculator
from kefe_api.modules.decision.normative_models import (
    NormativeModelsCalculator,
    NormativePhilosophy,
)
from kefe_api.modules.decision.policy_simulator import (
    EquilibriumState,
    PolicySimulatorCalculator,
)
from kefe_api.modules.decision.process_analysis import ProcessAnalysisCalculator
from kefe_api.modules.decision.responsibility_analysis import (
    ResponsibilityAnalysisCalculator,
)
from kefe_api.modules.decision.segment_distribution import (
    PrivacySafeSegmentDistributionService,
)
from kefe_api.modules.decision.stakeholder_distribution import (
    StakeholderDistributionService,
)

case_analytics_router = APIRouter(prefix="/v1/cases", tags=["Case Analytics"])

_OBJECTION_SERVICE = CaseObjectionService()
_CORRECTION_SERVICE = CaseCorrectionHistoryService()

# Seed default objection
_default_case_id = UUID("22222222-2222-4222-8222-222222222222")
_OBJECTION_SERVICE.submit_objection(
    case_version_id=_default_case_id,
    reason_category=ObjectionCategory.EDITORIAL_BIAS_FRAMING,
    statement="Seçenek kurgusu belirli bir ahlaki önceliği diğerine göre daha avantajlı gösterecek şekilde dil yönlendirmesi içermektedir.",
    supporting_evidence_url="https://kefe.org/delil/secenek-tarafsizligi",
)

# Seed default correction
_CORRECTION_SERVICE.log_correction(
    case_version_id=_default_case_id,
    correction_type=CorrectionType.FACTUAL_UPDATE,
    severity=CorrectionSeverity.MINOR,
    summary="Yasal mevzuat referans madde numarası güncellendi.",
    editorial_rationale="2026 revizyonu uyarınca mevzuat maddesi yeniden numaralandırılmıştır.",
    previous_text="Madde 14 uyarınca",
    corrected_text="Madde 16/A uyarınca",
)


class ObjectionCreateRequest(BaseModel):
    reason_category: ObjectionCategory
    statement: str
    supporting_evidence_url: str | None = None


class PolicyEvaluateRequest(BaseModel):
    knob_value: float = Field(..., ge=0.0, le=100.0)
    policy_knob_name: str = Field(..., min_length=3)


@case_analytics_router.get("/{case_version_id}/objections")
def list_case_objections(case_version_id: UUID) -> list[dict[str, Any]]:
    items = _OBJECTION_SERVICE.get_objections_for_case(case_version_id)
    return [
        {
            "objection_id": str(item.objection_id),
            "case_version_id": str(item.case_version_id),
            "reason_category": item.reason_category.value,
            "statement": item.statement,
            "status": item.status.value,
            "created_at": item.created_at.isoformat(),
            "supporting_evidence_url": item.supporting_evidence_url,
            "resolution_note": item.resolution_note,
        }
        for item in items
    ]


@case_analytics_router.post("/{case_version_id}/objections", status_code=201)
def submit_case_objection(
    case_version_id: UUID,
    body: ObjectionCreateRequest,
) -> dict[str, Any]:
    item = _OBJECTION_SERVICE.submit_objection(
        case_version_id=case_version_id,
        reason_category=body.reason_category,
        statement=body.statement,
        supporting_evidence_url=body.supporting_evidence_url,
    )
    return {
        "objection_id": str(item.objection_id),
        "case_version_id": str(item.case_version_id),
        "reason_category": item.reason_category.value,
        "statement": item.statement,
        "status": item.status.value,
        "created_at": item.created_at.isoformat(),
        "supporting_evidence_url": item.supporting_evidence_url,
        "resolution_note": item.resolution_note,
    }


@case_analytics_router.get("/{case_version_id}/quality-checklist")
def get_quality_checklist(case_version_id: UUID) -> dict[str, Any]:
    evaluator = CaseQualityChecklistEvaluator()
    return evaluator.evaluate(str(case_version_id)).to_dict()


@case_analytics_router.get("/{case_version_id}/consensus-divergence")
def get_consensus_divergence(
    case_version_id: UUID,
    distribution_json: str | None = Query(None),
) -> dict[str, Any]:
    if distribution_json:
        try:
            dist = json.loads(distribution_json)
            if not isinstance(dist, dict):
                raise ValueError("Distribution must be a JSON object")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid distribution_json format")
    else:
        dist = {"opt_a": 0.55, "opt_b": 0.45}

    result = ConsensusDivergenceClassifier.classify(case_version_id, dist)
    return {
        "case_version_id": str(case_version_id),
        "classification": result.classification.value,
        "leading_share": result.leading_share,
        "margin_of_divergence": result.margin_of_divergence,
        "label_tr": "Kolektif Uzlaşı / Ayrışma Dağılımı",
        "label_en": "Collective Consensus / Divergence Distribution",
        "description_tr": "Karar tercihlerinin topluluk genelindeki dağılımı ve kutuplaşma düzeyi ölçülmüştür.",
        "description_en": "Measures distribution and polarization levels of choices across the community.",
    }


@case_analytics_router.get("/{case_version_id}/corrections")
def get_case_corrections(case_version_id: UUID) -> dict[str, Any]:
    return _CORRECTION_SERVICE.get_history(case_version_id).to_dict()


@case_analytics_router.get("/{case_version_id}/expert-public-gap")
def get_expert_public_gap(case_version_id: UUID) -> dict[str, Any]:
    return ExpertPublicGapService.get_gap_analysis(str(case_version_id)).to_dict()


@case_analytics_router.get("/{case_version_id}/incentive-map")
def get_incentive_map(case_version_id: UUID) -> dict[str, Any]:
    return IncentiveMapCalculator.compute_for_case(case_version_id).to_dict()


@case_analytics_router.get("/{case_version_id}/normative-models")
def get_normative_models(case_version_id: UUID) -> dict[str, Any]:
    opt_a = NormativeModelsCalculator.evaluate_option("A", 0.85, 0.40, 0.90, 0.70)
    opt_b = NormativeModelsCalculator.evaluate_option("B", 0.45, 0.95, 0.35, 0.80)
    res = NormativeModelsCalculator.evaluate_case(case_version_id, [opt_a, opt_b])

    philosophies_tr = {
        NormativePhilosophy.UTILITARIAN_MAX_WELFARE.value: "En fazla sayıda insan için en yüksek toplam faydayı hedefler.",
        NormativePhilosophy.DEONTOLOGICAL_CATEGORICAL_RIGHTS.value: "Sonuçtan bağımsız olarak temel hak ve ahlaki ödevleri üstün tutar.",
        NormativePhilosophy.RAWLSIAN_MAXIMIN_EQUITY.value: "Toplumun en dezavantajlı kesiminin durumunu maksimize eder (fark ilkesi).",
        NormativePhilosophy.VIRTUE_ETHICS_CHARACTER.value: "Eylemin ardındaki erdem, basiret ve karakter bütünlüğünü esas alır.",
    }
    philosophies_en = {
        NormativePhilosophy.UTILITARIAN_MAX_WELFARE.value: "Maximizes net well-being across all stakeholders.",
        NormativePhilosophy.DEONTOLOGICAL_CATEGORICAL_RIGHTS.value: "Upholds categorical rights regardless of outcomes.",
        NormativePhilosophy.RAWLSIAN_MAXIMIN_EQUITY.value: "Maximizes outcomes for the least advantaged.",
        NormativePhilosophy.VIRTUE_ETHICS_CHARACTER.value: "Emphasizes moral character, prudence, and civic virtue.",
    }

    return {
        "case_version_id": str(case_version_id),
        "evaluations": [
            {
                "option_code": e.option_code,
                "dominant_philosophy": e.dominant_philosophy.value,
                "utilitarian_score": e.utilitarian_score,
                "deontological_score": e.deontological_score,
                "rawlsian_score": e.rawlsian_score,
                "virtue_score": e.virtue_score,
            }
            for e in res.evaluations
        ],
        "philosophies_explained_tr": philosophies_tr,
        "philosophies_explained_en": philosophies_en,
    }


@case_analytics_router.get("/{case_version_id}/perspective-clusters")
def get_perspective_clusters(case_version_id: UUID) -> dict[str, Any]:
    raw_clusters = [
        {
            "archetype": PerspectiveArchetype.NEAR_CONSENSUS.value,
            "core_thesis": "Acil ihtiyaçlar gözetilerek kademeli ve esnek geçiş sağlanmalıdır.",
            "argument_count": 520,
        },
        {
            "archetype": PerspectiveArchetype.OPPOSING_PRINCIPLE.value,
            "core_thesis": "Temel yurttaş hakları ve mahremiyet hiçbir koşulda pazarlık konusu yapılamaz.",
            "argument_count": 310,
        },
        {
            "archetype": PerspectiveArchetype.BRIDGE_SYNTHESIS.value,
            "core_thesis": "Bireysel fedakarlık yerine kamusal altyapı ve kurumsal kapasite genişletilmelidir.",
            "argument_count": 170,
        },
    ]
    result = MultiPartyPerspectiveClusteringService.cluster_case_perspectives(
        case_version_id, raw_clusters
    )
    return {
        "case_version_id": str(case_version_id),
        "total_arguments_clustered": result.total_arguments,
        "clusters": [
            {
                "cluster_id": str(c.cluster_id),
                "case_version_id": str(c.case_version_id),
                "archetype": c.archetype.value,
                "core_thesis": c.core_thesis,
                "argument_count": c.argument_count,
                "support_percentage": c.support_percentage,
            }
            for c in result.clusters
        ],
    }


@case_analytics_router.get("/{case_version_id}/policy-simulations")
def get_default_policy_simulation(case_version_id: UUID) -> dict[str, Any]:
    res = PolicySimulatorCalculator.simulate(
        simulation_id=f"SIM-{str(case_version_id)[:8]}",
        case_version_id=case_version_id,
        policy_knob_name="Toplu Taşıma Sübvansiyon Oranı",
        knob_value=50.0,
        fiscal_score=0.72,
        social_score=0.81,
        environmental_score=0.68,
    )
    return {
        "simulation_id": res.simulation_id,
        "case_version_id": str(res.case_version_id),
        "policy_knob_name": res.policy_knob_name,
        "knob_value": res.knob_value,
        "fiscal_score": res.fiscal_score,
        "social_score": res.social_score,
        "environmental_score": res.environmental_score,
        "equilibrium_state": res.equilibrium_state.value,
    }


@case_analytics_router.post("/{case_version_id}/policy-simulations/evaluate")
def evaluate_policy_simulation(
    case_version_id: UUID,
    body: PolicyEvaluateRequest,
) -> dict[str, Any]:
    val = body.knob_value
    fiscal = max(0.1, round(1.0 - (val / 150.0), 2))
    social = min(1.0, round(0.3 + (val / 140.0), 2))
    env = min(1.0, round(0.4 + (val / 200.0), 2))

    res = PolicySimulatorCalculator.simulate(
        simulation_id=f"SIM-{str(case_version_id)[:8]}",
        case_version_id=case_version_id,
        policy_knob_name=body.policy_knob_name,
        knob_value=val,
        fiscal_score=fiscal,
        social_score=social,
        environmental_score=env,
    )
    return {
        "simulation_id": res.simulation_id,
        "case_version_id": str(res.case_version_id),
        "policy_knob_name": res.policy_knob_name,
        "knob_value": res.knob_value,
        "fiscal_score": res.fiscal_score,
        "social_score": res.social_score,
        "environmental_score": res.environmental_score,
        "equilibrium_state": res.equilibrium_state.value,
    }


@case_analytics_router.get("/{case_version_id}/process-analysis")
def get_process_analysis(case_version_id: UUID) -> dict[str, Any]:
    return ProcessAnalysisCalculator.compute_for_case(case_version_id).to_dict()


@case_analytics_router.get("/{case_version_id}/responsibility-analysis")
def get_responsibility_analysis(case_version_id: UUID) -> dict[str, Any]:
    return ResponsibilityAnalysisCalculator.compute_for_case(case_version_id).to_dict()


@case_analytics_router.get("/{case_version_id}/segment-distributions")
def get_segment_distributions(case_version_id: UUID) -> dict[str, Any]:
    return PrivacySafeSegmentDistributionService.get_segment_distribution(
        str(case_version_id)
    ).to_dict()


@case_analytics_router.get("/{case_version_id}/stakeholder-distributions")
def get_stakeholder_distributions(case_version_id: UUID) -> dict[str, Any]:
    return StakeholderDistributionService.get_stakeholder_distribution(
        str(case_version_id)
    ).to_dict()
