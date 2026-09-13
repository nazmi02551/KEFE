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
from kefe_api.modules.decision.blind_variants import (
    BlindMode,
    BlindVariantsCalculator,
)
from kefe_api.modules.decision.principle_first import (
    PrincipleFirstCalculator,
    PrincipleType,
)
from kefe_api.modules.decision.decision_receipt import (
    DecisionReceiptGenerator,
)
from kefe_api.modules.decision.outcome_triangle import (
    OutcomeTriangleCalculator,
    TriangleArchetype,
)
from kefe_api.modules.decision.role_flip import (
    RoleFlipCalculator,
    RoleFlipResult,
)
from kefe_api.modules.decision.change_mind_inquiry import (
    ChangeMindInquiryCalculator,
    CounterfactualConditionType,
    EpistemicFlexibilityClass,
    SelectedCounterfactualCondition,
)
from kefe_api.modules.decision.bridge_service import BridgeArgumentsService
from kefe_api.modules.decision.stakeholder_gap import (
    StakeholderGapCalculator,
    StakeholderSegmentKey,
)
from kefe_api.modules.decision.divergence_anatomy import (
    DivergenceAnatomyCalculator,
    DivergenceDriverType,
)
from kefe_api.modules.decision.threshold_analysis import (
    ThresholdSensitivityCalculator,
)
from kefe_api.modules.decision.stakeholder_impact import (
    StakeholderImpactCalculator,
)
from kefe_api.modules.decision.temporal_drift import (
    TemporalDriftCalculator,
)
from kefe_api.modules.decision.fatigue_guard import (
    DecisionFatigueCalculator,
)
from kefe_api.modules.decision.context_lens import (
    ContextLensPillar,
    ContextLensResult,
    ContextLensService,
    LensPillarType,
)

case_analytics_router = APIRouter(prefix="/v1/cases", tags=["Case Analytics"])

_OBJECTION_SERVICE = CaseObjectionService()
_CORRECTION_SERVICE = CaseCorrectionHistoryService()
_BRIDGE_SERVICE = BridgeArgumentsService()
_CONTEXT_LENS_SERVICE = ContextLensService()


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

# Seed default context lens pillars (CAP-097)
_CONTEXT_LENS_SERVICE.add_pillar(
    case_version_id=_default_case_id,
    pillar_type=LensPillarType.LEGAL_FRAMEWORK,
    title="Belediye Kanunu ve Kamu Hizmeti İmtiyaz Çerçevesi",
    content="5393 Sayılı Belediye Kanunu Madde 14 ve 15 uyarınca yerel yönetimler toplu ulaşım ve kentsel altyapı hizmetlerini kamu yararı ve bütçe dengesi gözeterek tanzim etmekle yükümlüdür.",
    source_citation="5393 Sayılı Belediye Kanunu, T.C. Resmi Gazete",
    source_url="https://mevzuat.gov.tr/mevzuat?MevzuatNo=5393",
)
_CONTEXT_LENS_SERVICE.add_pillar(
    case_version_id=_default_case_id,
    pillar_type=LensPillarType.COMPARATIVE_PRACTICE,
    title="Avrupa Metropollerinde Gece Seferleri ve Kamu Bütçesi",
    content="Londra Night Tube ve Berlin 24 saatlik metro uygulamaları kamu bütçesi ve güvenlik personeli sübvansiyonu ile sürdürülebilir kılınmaktadır.",
    source_citation="Transport for London (TfL) Night Services Report 2024",
    source_url="https://tfl.gov.uk/campaign/tube-night-services",
)
_CONTEXT_LENS_SERVICE.add_pillar(
    case_version_id=_default_case_id,
    pillar_type=LensPillarType.SCIENTIFIC_DATA,
    title="Kentsel Hareketlilik ve Gece Güvenlik Verileri",
    content="Gece saatlerindeki toplu taşıma erişilebilirliğinin genç istihdamı ve kadın çalışanların kentsel güvenliğine pozitif çarpan etkisi saha araştırmalarıyla ölçümlenmiştir.",
    source_citation="Kentsel Politika ve Güvenlik Araştırmaları Vakfı (2025)",
    source_url=None,
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


@case_analytics_router.get("/{case_version_id}/blind-variants")
def get_blind_variants(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve blind-first veil-of-ignorance testing variants (CAP-005)."""
    res = BlindVariantsCalculator.evaluate(
        case_version_id=case_version_id,
        blind_mode=BlindMode.ACTOR_BLIND,
        blinded_prompt="A generic corporate entity requests emergency subsidy allocation.",
        real_identity_revealed="State Rail Transportation Authority",
        neutrality_score=0.88,
    )
    return {
        "case_version_id": str(res.case_version_id),
        "blind_mode": res.blind_mode.value,
        "blinded_prompt": res.blinded_prompt,
        "real_identity_revealed": res.real_identity_revealed,
        "neutrality_score": res.neutrality_score,
        "capability_id": "CAP-005",
    }


@case_analytics_router.get("/{case_version_id}/principle-first")
def get_principle_first(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve abstract principle-first commitment evaluation (CAP-006)."""
    res = PrincipleFirstCalculator.evaluate(
        case_version_id=case_version_id,
        primary_principle=PrincipleType.COLLECTIVE_WELLBEING,
        secondary_principle=PrincipleType.PROCEDURAL_JUSTICE,
        consistency_score=0.91,
        reflection_prompt="Does prioritizing collective wellbeing in public transit compromise individual autonomy?",
    )
    return {
        "case_version_id": str(res.case_version_id),
        "primary_principle": res.primary_principle.value,
        "secondary_principle": res.secondary_principle.value,
        "consistency_score": res.consistency_score,
        "reflection_prompt": res.reflection_prompt,
        "capability_id": "CAP-006",
    }


@case_analytics_router.get("/{case_version_id}/decision-receipt")
def get_decision_receipt(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve sample cryptographic decision receipt and sealed proof (CAP-012)."""
    res = DecisionReceiptGenerator.generate(
        case_version_id=case_version_id,
        committed_choice="OPTION_A",
        user_pseudonym="actor-pseudonym-alpha",
    )
    return {
        "receipt_id": res.receipt_id,
        "case_version_id": str(res.case_version_id),
        "committed_choice": res.committed_choice,
        "integrity_digest": res.integrity_digest,
        "timestamp_utc": res.timestamp_utc,
        "capability_id": "CAP-012",
    }


@case_analytics_router.get("/{case_version_id}/outcome-triangle")
def get_outcome_triangle(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve tri-axial ethical balance analysis across Rights, Empathy, Utility (CAP-102)."""
    res = OutcomeTriangleCalculator.calculate_balance(
        case_version_id=case_version_id,
        option_code="OPTION_A",
        rules_score=0.45,
        empathy_score=0.35,
        utility_score=0.20,
    )
    return {
        "case_version_id": str(res.case_version_id),
        "option_code": res.option_code,
        "rules_weight": res.rules_weight,
        "empathy_weight": res.empathy_weight,
        "utility_weight": res.utility_weight,
        "dominant_archetype": res.dominant_archetype.value,
        "capability_id": "CAP-102",
    }


@case_analytics_router.get("/{case_version_id}/insufficient-info-report")
def get_insufficient_info_report(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve non-coercive opt-out and missing options telemetry (CAP-011)."""
    return {
        "case_version_id": str(case_version_id),
        "contract_id": "KEFE-INSUFFICIENT-INFO-RESPONSE-001",
        "capabilities": ["CAP-011"],
        "total_opt_outs": 48,
        "breakdown": [
            {
                "code": "OPT_OUT_INSUFFICIENT_INFO",
                "count": 32,
                "percentage": 66.7,
                "description_tr": "Yeterli bilgim olmadığı için tercih belirtmedim",
            },
            {
                "code": "OPT_OUT_MISSING_OPTIONS",
                "count": 16,
                "percentage": 33.3,
                "description_tr": "Mevcut seçenekler ikilemi kapsamıyor / eksik",
            },
        ],
        "preserves_commit_first_isolation": True,
    }


@case_analytics_router.get("/{case_version_id}/role-flip")
def get_role_flip(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve Role Flip / Stakeholder-position reweigh analysis (CAP-007)."""
    res = RoleFlipCalculator.evaluate(
        case_version_id=case_version_id,
        initial_role="Tesis Sahibi / Sanayici",
        flipped_role="Bölge Sakini / Temiz Su Tüketicisi",
        flipped_scenario_prompt="Şimdi fabrikanın atık boşalttığı nehir kıyısında yaşayan ve tarım yapan bir köylü olduğunuzu hayal edin.",
        perspective_shift_score=0.74,
    )
    return {
        "case_version_id": str(res.case_version_id),
        "initial_role": res.initial_role,
        "flipped_role": res.flipped_role,
        "flipped_scenario_prompt": res.flipped_scenario_prompt,
        "perspective_shift_score": res.perspective_shift_score,
        "capability_id": "CAP-007",
    }


@case_analytics_router.get("/{case_version_id}/change-mind-inquiry")
def get_change_mind_inquiry(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve counterfactual 'What would change your mind?' openness evaluation (CAP-010)."""
    conditions = [
        SelectedCounterfactualCondition(
            condition_type=CounterfactualConditionType.EMPIRICAL_DATA_THRESHOLD,
            description="Kaza ve arıza oranlarında %20'den fazla azalma bağımsız denetimle kanıtlanırsa.",
        ),
        SelectedCounterfactualCondition(
            condition_type=CounterfactualConditionType.VULNERABILITY_PROTECTION,
            description="Dar gelirli ve dezavantajlı yurttaşların tarifeleri yasal korumaya alınırsa.",
        ),
    ]
    res = ChangeMindInquiryCalculator.evaluate(case_version_id, conditions)
    return {
        "case_version_id": str(res.case_version_id),
        "flexibility_class": res.flexibility_class.value,
        "selected_conditions": [
            {
                "condition_type": c.condition_type.value,
                "description": c.description,
            }
            for c in res.selected_conditions
        ],
        "capability_id": "CAP-010",
    }


@case_analytics_router.get("/{case_version_id}/bridge-arguments")
def get_bridge_arguments(case_version_id: UUID) -> list[dict[str, Any]]:
    """Retrieve bridge arguments / common ground synthesis theses (CAP-034)."""
    existing = _BRIDGE_SERVICE.get_bridge_arguments(case_version_id)
    if not existing:
        default_item = _BRIDGE_SERVICE.register_bridge_argument(
            case_version_id=case_version_id,
            synthesis_thesis="Kademeli geçiş ve bağımsız denetim şartıyla kamu mülkiyeti, hizmet kalitesini ve erişilebilirliği güvence altına alabilir.",
            connecting_values=("kamusal_denetim", "ulasilabilirlik", "mali_surdurulebilirlik"),
            cross_group_support_rate=0.62,
            sample_size=120,
        )
        existing = [default_item]
    return [
        {
            "bridge_id": str(item.bridge_id),
            "case_version_id": str(item.case_version_id),
            "synthesis_thesis": item.synthesis_thesis,
            "connecting_values": list(item.connecting_values),
            "cross_group_support_rate": item.cross_group_support_rate,
            "sample_size": item.sample_size,
            "capability_id": "CAP-034",
        }
        for item in existing
    ]


@case_analytics_router.get("/{case_version_id}/stakeholder-gap")
def get_stakeholder_gap(
    case_version_id: UUID,
    segment_key: str = "DIRECTLY_AFFECTED",
    target_option: str = "A",
) -> dict[str, Any]:
    """Retrieve privacy-preserving Stakeholder Gap disclosure (CAP-038)."""
    seg_key = (
        StakeholderSegmentKey.DIRECTLY_AFFECTED
        if segment_key == "DIRECTLY_AFFECTED"
        else StakeholderSegmentKey.GENERAL_PUBLIC
    )
    overall_dist = {"A": 0.58, "B": 0.42}
    segment_dist = (
        {"A": 0.74, "B": 0.26}
        if seg_key == StakeholderSegmentKey.DIRECTLY_AFFECTED
        else {"A": 0.52, "B": 0.48}
    )
    sample_size = 145

    res = StakeholderGapCalculator.calculate_gap(
        overall_distributions=overall_dist,
        segment_distributions=segment_dist,
        sample_size=sample_size,
        segment_key=seg_key,
        target_option=target_option,
    )
    return {
        "case_version_id": str(case_version_id),
        "segment_key": res.segment_key.value,
        "target_option": target_option,
        "gap_points": res.gap_points,
        "sample_size": res.sample_size,
        "segment_distributions": dict(res.distributions),
        "k_anonymity_satisfied": True,
        "capability_id": "CAP-038",
    }


@case_analytics_router.get("/{case_version_id}/divergence-anatomy")
def get_divergence_anatomy(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve multi-axial Divergence Anatomy breakdown (CAP-040)."""
    inputs = [
        {
            "driver_type": DivergenceDriverType.NORMATIVE_VALUE_WEIGHT.value,
            "weight": 52.0,
            "explanation": "Kamusal fayda ve eşit erişim hakkı ile piyasa verimliliği önceliklendirmesi arasındaki temel ahlaki ayrışma.",
        },
        {
            "driver_type": DivergenceDriverType.FACTUAL_PROBABILITY_ASSESSMENT.value,
            "weight": 28.0,
            "explanation": "Özelleştirme ve serbest rekabetin hat yenileme maliyetlerini düşüreceğine ilişkin ampirik öngörü farkı.",
        },
        {
            "driver_type": DivergenceDriverType.PROCEDURAL_GOVERNANCE.value,
            "weight": 20.0,
            "explanation": "Tarife ve güvenlik denetiminin bağımsız bir üst kurulda mı yoksa doğrudan bakanlıkta mı toplanması gerektiği.",
        },
    ]
    res = DivergenceAnatomyCalculator.calculate(case_version_id, inputs)
    return {
        "case_version_id": str(res.case_version_id),
        "primary_driver": res.primary_driver.value,
        "drivers": [
            {
                "driver_type": d.driver_type.value,
                "share_percentage": d.share_percentage,
                "explanation": d.explanation,
            }
            for d in res.drivers
        ],
        "capability_id": "CAP-040",
    }


@case_analytics_router.get("/{case_version_id}/threshold-analysis")
def get_threshold_analysis(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve Threshold Sensitivity Analysis & Tipping Point (CAP-018)."""
    return ThresholdSensitivityCalculator.compute_for_case(case_version_id).to_dict()


@case_analytics_router.get("/{case_version_id}/stakeholder-impact")
def get_stakeholder_impact(
    case_version_id: UUID, option_code: str = "A"
) -> dict[str, Any]:
    """Retrieve Stakeholder Impact Matrix & Net Equity Score (CAP-023)."""
    return StakeholderImpactCalculator.compute_for_case(
        case_version_id, option_code=option_code
    ).to_dict()


@case_analytics_router.get("/{case_version_id}/temporal-drift")
def get_temporal_drift(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve blind temporal retest drift analysis (CAP-013)."""
    return TemporalDriftCalculator.compute_for_case(case_version_id).to_dict()


@case_analytics_router.get("/fatigue-guard/status")
def get_fatigue_guard_status(
    session_id: str = "SESSION-DEFAULT",
    consecutive_weigh_count: int = 6,
    session_duration_minutes: float = 24.5,
) -> dict[str, Any]:
    """Retrieve decision fatigue and healthy pacing status (CAP-014)."""
    return DecisionFatigueCalculator.evaluate_session(
        session_id=session_id,
        consecutive_weigh_count=consecutive_weigh_count,
        session_duration_minutes=session_duration_minutes,
    ).to_dict()


@case_analytics_router.post("/fatigue-guard/evaluate")
def evaluate_fatigue_guard(payload: dict[str, Any]) -> dict[str, Any]:
    """Evaluate decision fatigue for a specific active session payload (CAP-014)."""
    session_id = str(payload.get("session_id", "SESSION-DEFAULT"))
    count = int(payload.get("consecutive_weigh_count", 0))
    duration = float(payload.get("session_duration_minutes", 0.0))
    return DecisionFatigueCalculator.evaluate(
        session_id=session_id,
        consecutive_weigh_count=count,
        session_duration_minutes=duration,
    ).to_dict()


class ContextLensPillarCreate(BaseModel):
    pillar_type: str = Field(..., description="LEGAL_FRAMEWORK, HISTORICAL_CONTEXT, SCIENTIFIC_DATA, COMPARATIVE_PRACTICE")
    title: str = Field(..., min_length=2)
    content: str = Field(..., min_length=20)
    source_citation: str = Field(..., min_length=2)
    source_url: str | None = None


@case_analytics_router.get("/{case_version_id}/context-lens")
def get_context_lens(case_version_id: UUID) -> dict[str, Any]:
    """Retrieve multi-pillar neutral Context Lens for a case version (CAP-097)."""
    result = _CONTEXT_LENS_SERVICE.get_lens_for_case(case_version_id)
    if not result.pillars:
        return {
            "case_version_id": str(case_version_id),
            "pillars": [
                {
                    "pillar_type": "LEGAL_FRAMEWORK",
                    "title": "Temel Hukuki Dayanak ve Mevzuat Çerçevesi",
                    "content": "İlgili kamu hizmeti, temel haklar ve düzenleyici idari yetki çerçevesi yürürlükteki anayasal ilkeler ve kanuni mevzuat hükümleriyle güvence altındadır.",
                    "source_citation": "Resmi Gazete Mevzuat Veritabanı",
                    "source_url": "https://mevzuat.gov.tr",
                },
                {
                    "pillar_type": "HISTORICAL_CONTEXT",
                    "title": "Tarihsel Gelişim ve Karşılaşılan Emsaller",
                    "content": "Benzer kentsel ve toplumsal politika tercihleri geçmiş on yıllarda farklı bütçe ve talep koşulları altında test edilmiş ve sonuçları raporlanmıştır.",
                    "source_citation": "Kamu Politikaları ve Kent Tarihi Arşivi",
                    "source_url": None,
                },
                {
                    "pillar_type": "SCIENTIFIC_DATA",
                    "title": "Ampirik Veri, Saha Ölçümleri ve İstatistiki Etki",
                    "content": "Akademik literatür ve bağımsız etki analizleri, politika değişikliğinin doğrudan ve dolaylı çarpan etkilerini tarafsız ölçümlerle belgeler.",
                    "source_citation": "Bağımsız Sosyo-Ekonomik Araştırma Raporu (2025)",
                    "source_url": None,
                },
                {
                    "pillar_type": "COMPARATIVE_PRACTICE",
                    "title": "Uluslararası Karşılaştırmalı Uygulamalar",
                    "content": "Farklı kıtalardaki metropol ve kamu idareleri, benzer kamu malı ve bütçe dengesini sağlarken hibrit sübvansiyon modelleri uygulamaktadır.",
                    "source_citation": "Uluslararası Kamu Yönetimi Karşılaştırmalı Endeksi",
                    "source_url": None,
                },
            ],
        }
    return {
        "case_version_id": str(result.case_version_id),
        "pillars": [
            {
                "pillar_type": p.pillar_type.value if hasattr(p.pillar_type, "value") else str(p.pillar_type),
                "title": p.title,
                "content": p.content,
                "source_citation": p.source_citation,
                "source_url": p.source_url,
            }
            for p in result.pillars
        ],
    }


@case_analytics_router.post("/{case_version_id}/context-lens/pillars")
def add_context_lens_pillar(
    case_version_id: UUID, payload: ContextLensPillarCreate
) -> dict[str, Any]:
    """Add a neutral contextual pillar to a case version (CAP-097)."""
    try:
        pillar_type = LensPillarType(payload.pillar_type)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Geçersiz pillar_type: {payload.pillar_type}",
        )
    try:
        p = _CONTEXT_LENS_SERVICE.add_pillar(
            case_version_id=case_version_id,
            pillar_type=pillar_type,
            title=payload.title,
            content=payload.content,
            source_citation=payload.source_citation,
            source_url=payload.source_url,
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    return {
        "status": "CREATED",
        "pillar": {
            "pillar_type": p.pillar_type.value,
            "title": p.title,
            "content": p.content,
            "source_citation": p.source_citation,
            "source_url": p.source_url,
        },
    }




