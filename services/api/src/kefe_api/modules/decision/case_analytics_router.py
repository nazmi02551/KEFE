from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from kefe_api.modules.decision.case_objection import (
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
)
from kefe_api.modules.decision.expert_public_gap import ExpertPublicGapService
from kefe_api.modules.decision.incentive_map import IncentiveMapCalculator
from kefe_api.modules.decision.normative_models import (
    NormativeModelsCalculator,
    NormativePhilosophy,
)
from kefe_api.modules.decision.policy_simulator import (
    PolicySimulatorCalculator,
)
from kefe_api.modules.decision.process_analysis import ProcessAnalysisCalculator
from kefe_api.modules.decision.responsibility_analysis import (
    ResponsibilityAnalysisCalculator,
)
from kefe_api.modules.decision.budget_tradeoff_simulator import (
    BudgetTradeoffSimulator,
    TradeoffProfile,
)
from kefe_api.modules.decision.community_dilemma_proposals import (
    CommunityDilemmaProposalsService,
    CurationState,
)
from kefe_api.modules.decision.historical_retrospective import (
    HistoricalEra,
    HistoricalRetrospectiveEngine,
)
from kefe_api.modules.decision.observe_mode_exploration import (
    ExplorationMode,
    ObserveModeService,
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


class ObjectionDecisionRequest(BaseModel):
    decision: str
    resolution_note: str = Field(..., min_length=10)


class CorrectionCreateRequest(BaseModel):
    correction_type: CorrectionType
    severity: CorrectionSeverity
    summary: str = Field(..., min_length=5)
    editorial_rationale: str = Field(..., min_length=10)
    previous_text: str | None = None
    corrected_text: str | None = None


class PolicyEvaluateRequest(BaseModel):
    knob_value: float = Field(..., ge=0.0, le=100.0)
    policy_knob_name: str = Field(..., min_length=3)


class BudgetTradeoffEvaluateRequest(BaseModel):
    healthcare_pct: int = Field(..., ge=0, le=100)
    education_pct: int = Field(..., ge=0, le=100)
    infrastructure_pct: int = Field(..., ge=0, le=100)
    green_transition_pct: int = Field(..., ge=0, le=100)


class ObserveSessionCreateRequest(BaseModel):
    exploration_mode: str = "OBSERVE_ONLY"


class CommunityProposalCreateRequest(BaseModel):
    proposed_title: str = Field(..., min_length=5)
    proposed_context: str = Field(..., min_length=10)


_PROPOSALS_STORE: list[dict[str, Any]] = [
    {
        "proposal_id": "PROP-001",
        "proposed_title": "Kent İçi Ulaşımda Gece Seferlerinin Ücretsiz Olması",
        "proposed_context": "Gece vardiyasında çalışan işçiler ve gençlerin güvenliği için kamu sübvansiyonu sağlanmalıdır.",
        "curation_state": "COMMUNITY_PEER_REVIEW",
        "neutrality_score": 0.85,
        "supporter_count": 142,
    }
]


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


@case_analytics_router.post("/{case_version_id}/objections/{objection_id}/decision")
def decide_case_objection(
    case_version_id: UUID,
    objection_id: UUID,
    body: ObjectionDecisionRequest,
) -> dict[str, Any]:
    new_status = (
        ObjectionStatus.ACCEPTED_CORRECTION_FILED
        if body.decision == "ACCEPT_AND_FILE_CORRECTION"
        else ObjectionStatus.REJECTED_WITH_REASON
    )
    resolved = _OBJECTION_SERVICE.resolve_objection(
        objection_id=objection_id,
        new_status=new_status,
        resolution_note=body.resolution_note,
    )
    if not resolved:
        raise HTTPException(status_code=404, detail="Objection not found")
    return {
        "objection_id": str(resolved.objection_id),
        "status": resolved.status.value,
        "resolution_note": resolved.resolution_note,
        "resolved_at": datetime.now(UTC).isoformat(),
        "audit_hash": f"sha256:{resolved.objection_id}",
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
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid distribution_json format") from exc
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


@case_analytics_router.post("/{case_version_id}/corrections", status_code=201)
def add_case_correction(
    case_version_id: UUID,
    body: CorrectionCreateRequest,
) -> dict[str, Any]:
    item = _CORRECTION_SERVICE.log_correction(
        case_version_id=case_version_id,
        correction_type=body.correction_type,
        severity=body.severity,
        summary=body.summary,
        editorial_rationale=body.editorial_rationale,
        previous_text=body.previous_text,
        corrected_text=body.corrected_text,
    )
    return {
        "correction_id": str(item.correction_id),
        "case_version_id": str(item.case_version_id),
        "correction_type": item.correction_type.value,
        "severity": item.severity.value,
        "summary": item.summary,
        "editorial_rationale": item.editorial_rationale,
        "timestamp": item.timestamp.isoformat(),
        "previous_text": item.previous_text,
        "corrected_text": item.corrected_text,
    }


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


@case_analytics_router.get("/{case_version_id}/budget-tradeoff")
def get_default_budget_tradeoff(case_version_id: UUID) -> dict[str, Any]:
    res = BudgetTradeoffSimulator.evaluate(
        tradeoff_id=f"TRD-{str(case_version_id)[:8]}",
        case_version_id=case_version_id,
        healthcare_pct=30,
        education_pct=25,
        infrastructure_pct=25,
        green_transition_pct=20,
    )
    return {
        "tradeoff_id": res.tradeoff_id,
        "case_version_id": str(res.case_version_id),
        "healthcare_pct": res.healthcare_pct,
        "education_pct": res.education_pct,
        "infrastructure_pct": res.infrastructure_pct,
        "green_transition_pct": res.green_transition_pct,
        "unallocated_pct": res.unallocated_pct,
        "tradeoff_profile": res.tradeoff_profile.value,
    }


@case_analytics_router.post("/{case_version_id}/budget-tradeoff/evaluate")
def evaluate_budget_tradeoff(
    case_version_id: UUID,
    body: BudgetTradeoffEvaluateRequest,
) -> dict[str, Any]:
    total = (
        body.healthcare_pct
        + body.education_pct
        + body.infrastructure_pct
        + body.green_transition_pct
    )
    if total > 100:
        raise HTTPException(
            status_code=400,
            detail=f"Total budget allocation cannot exceed 100%, got {total}%",
        )

    res = BudgetTradeoffSimulator.evaluate(
        tradeoff_id=f"TRD-{str(case_version_id)[:8]}",
        case_version_id=case_version_id,
        healthcare_pct=body.healthcare_pct,
        education_pct=body.education_pct,
        infrastructure_pct=body.infrastructure_pct,
        green_transition_pct=body.green_transition_pct,
    )
    return {
        "tradeoff_id": res.tradeoff_id,
        "case_version_id": str(res.case_version_id),
        "healthcare_pct": res.healthcare_pct,
        "education_pct": res.education_pct,
        "infrastructure_pct": res.infrastructure_pct,
        "green_transition_pct": res.green_transition_pct,
        "unallocated_pct": res.unallocated_pct,
        "tradeoff_profile": res.tradeoff_profile.value,
    }


@case_analytics_router.get("/{case_version_id}/historical-retrospective")
def get_historical_retrospective(case_version_id: UUID) -> dict[str, Any]:
    res = HistoricalRetrospectiveEngine.evaluate(
        retrospective_id=f"RETRO-{str(case_version_id)[:8]}",
        case_version_id=case_version_id,
        historical_era=HistoricalEra.INDUSTRIAL_ERA,
        historical_year=1888,
        historical_event_name="Demiryolu Hatlarının Kamulaştırılması Kararı",
        actual_historical_decision="Özel imtiyazlı yabancı demiryolu şirketleri yerine kamu mülkiyeti ve tarifeli denetim modeli benimsenmiştir.",
        historical_consequence_summary="Ulaşım maliyetleri uzun vadede düşmüş, bölgesel entegrasyon hızlanmış ve kamusal denetim sağlanmıştır.",
    )
    return {
        "retrospective_id": res.retrospective_id,
        "case_version_id": str(res.case_version_id),
        "historical_era": res.historical_era.value,
        "historical_year": res.historical_year,
        "historical_event_name": res.historical_event_name,
        "actual_historical_decision": res.actual_historical_decision,
        "historical_consequence_summary": res.historical_consequence_summary,
    }


@case_analytics_router.post("/{case_version_id}/observe-session")
def create_observe_session(
    case_version_id: UUID,
    body: ObserveSessionCreateRequest | None = None,
) -> dict[str, Any]:
    mode_str = body.exploration_mode if body else "OBSERVE_ONLY"
    mode = (
        ExplorationMode.STUDY_AND_LEARN
        if mode_str == "STUDY_AND_LEARN"
        else ExplorationMode.OBSERVE_ONLY
    )
    res = ObserveModeService.start_session(
        session_id=f"OBS-{str(case_version_id)[:8]}",
        case_version_id=case_version_id,
        exploration_mode=mode,
        viewed_argument_count=0,
        viewed_evidence_count=0,
    )
    return {
        "session_id": res.session_id,
        "case_version_id": str(res.case_version_id),
        "exploration_mode": res.exploration_mode.value,
        "is_binding_vote": res.is_binding_vote,
        "viewed_argument_count": res.viewed_argument_count,
        "viewed_evidence_count": res.viewed_evidence_count,
    }


@case_analytics_router.get("/{case_version_id}/community-proposals")
def list_community_proposals(case_version_id: UUID) -> list[dict[str, Any]]:
    return _PROPOSALS_STORE


@case_analytics_router.post("/{case_version_id}/community-proposals", status_code=201)
def create_community_proposal(
    case_version_id: UUID,
    body: CommunityProposalCreateRequest,
) -> dict[str, Any]:
    proposal = CommunityDilemmaProposalsService.register_proposal(
        proposal_id=f"PROP-{len(_PROPOSALS_STORE) + 1:03d}",
        proposed_title=body.proposed_title,
        proposed_context=body.proposed_context,
        curation_state=CurationState.DRAFT_SUBMITTED,
        neutrality_score=0.75,
        supporter_count=1,
    )
    item = {
        "proposal_id": proposal.proposal_id,
        "proposed_title": proposal.proposed_title,
        "proposed_context": proposal.proposed_context,
        "curation_state": proposal.curation_state.value,
        "neutrality_score": proposal.neutrality_score,
        "supporter_count": proposal.supporter_count,
    }
    _PROPOSALS_STORE.append(item)
    return item
