from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from kefe_api.modules.decision.decision_receipt import DecisionReceiptGenerator
from kefe_api.modules.decision.source_diversity import (
    SourceDiversityCalculator,
    SourcePluralityCategory,
)


def build_analytical_perspectives(
    *,
    case_version_id: UUID,
    session_id: UUID,
    actor_id: UUID,
    committed_choice: str = "A",
) -> dict[str, Any]:
    now_utc = datetime.now(UTC)
    ts_str = now_utc.isoformat()

    user_pseudonym = str(actor_id)[:8]
    receipt = DecisionReceiptGenerator.generate(
        case_version_id=case_version_id,
        committed_choice=committed_choice,
        user_pseudonym=user_pseudonym,
        timestamp=now_utc,
    )

    return {
        "bridge_arguments": [
            {
                "argument_id": "bridge-1",
                "title": "Ortak Zemin Çözümü",
                "premise": "Acil ihtiyaca yanıt verirken şeffaf kural işletimi her iki tarafça makul bulunmaktadır.",
                "common_ground_score": 0.82,
                "opposing_acknowledgment": "Karşı tarafın süreç güvenliği kaygısı meşru kabul edilmiştir.",
            }
        ],
        "divergence_anatomy": {
            "case_version_id": str(case_version_id),
            "divergence_type": "VALUE_PRIORITIZATION",
            "primary_friction_point": "Katı Kural vs. Esnek Merhamet",
            "polarization_risk_score": 0.34,
            "resolution_leverage_point": "İstisnaların nesnel kriterlerle sınırlandırılması",
        },
        "depolarization_index": {
            "session_id": str(session_id),
            "baseline_polarization": 0.68,
            "deliberated_polarization": 0.42,
            "bridge_potential_score": 0.76,
            "shift_direction": "CONVERGENCE",
        },
        "deliberation_depth": {
            "session_id": str(session_id),
            "complexity_score": 0.85,
            "nuance_recognition_score": 0.78,
            "trade_off_awareness_score": 0.82,
            "depth_tier": "HIGH_REFLECTIVE",
        },
        "bot_shield": {
            "session_id": str(session_id),
            "anomaly_score": 0.04,
            "sybil_risk_tier": "VERIFIED_ORGANIC",
            "synthetic_patterns_detected": False,
            "integrity_status": "PASSED",
            "quarantined_bot_payloads_count": 0,
            "semantic_entropy_index": 0.94,
        },
        "threshold_analysis": {
            "case_version_id": str(case_version_id),
            "parameter_name": "Aciliyet Eşiği",
            "unit": "%",
            "tipping_point_threshold": 0.65,
            "curve_points": [
                {"parameter_value": 0.2, "acceptance_rate": 0.3},
                {"parameter_value": 0.5, "acceptance_rate": 0.6},
                {"parameter_value": 0.8, "acceptance_rate": 0.85},
            ],
        },
        "stakeholder_impact": {
            "case_version_id": str(case_version_id),
            "option_code": committed_choice,
            "net_equity_score": 15,
            "impact_items": [
                {
                    "group": "VULNERABLE_POPULATIONS",
                    "impact_type": "POSITIVE_DIRECT",
                    "impact_score": 8,
                    "description": "Acil durumdaki bireylerin korunması",
                },
                {
                    "group": "REGULATORY_BODIES",
                    "impact_type": "NEUTRAL",
                    "impact_score": 0,
                    "description": "Kurumsal prosedürlerin sürdürülmesi",
                },
            ],
        },
        "outcome_triangle": {
            "case_version_id": str(case_version_id),
            "option_code": committed_choice,
            "rules_weight": 0.35,
            "empathy_weight": 0.45,
            "utility_weight": 0.20,
            "dominant_archetype": "COMPASSION_FIRST",
        },
        "change_mind_inquiry": {
            "case_version_id": str(case_version_id),
            "flexibility_class": "OPEN_TO_EVIDENCE",
            "selected_conditions": [
                {
                    "condition_type": "EMPIRICAL_EVIDENCE",
                    "description": "Kaynak tahsisinde bağımsız hekim raporu bulunması",
                }
            ],
            "custom_falsification_note": "Nesnel önceliklendirme ölçütleri sağlandığında.",
        },
        "argument_strength": {
            "argument_id": "arg-1",
            "empirical_foundation_score": 0.82,
            "logical_consistency_score": 0.88,
            "representative_balance_score": 0.79,
            "composite_strength_score": 0.83,
            "strength_tier": "STRONG",
        },
        "fallacy_detection": {
            "argument_id": "arg-1",
            "has_fallacy": False,
            "overall_integrity_score": 0.95,
            "detected_fallacies": [],
        },
        "irreversibility_risk": {
            "case_version_id": str(case_version_id),
            "option_code": committed_choice,
            "reversibility_class": "SHORT_TERM_REVERSIBLE",
            "precautionary_risk_score": 0.22,
            "unwind_time_months": 1,
            "unwind_cost_factor": 1.1,
            "risk_summary": "Geçici tahsis modeli ile geri dönülebilirlik korunabilir.",
        },
        "unintended_consequences": {
            "case_version_id": str(case_version_id),
            "option_code": committed_choice,
            "overall_systemic_risk": "LOW",
            "consequences": [
                {
                    "consequence_type": "PROCEDURAL_DELAY",
                    "severity": "LOW",
                    "mitigation_feasibility": 0.85,
                    "description": "Kısa süreli inceleme süresinin uzaması",
                }
            ],
        },
        "proportionality_test": {
            "case_version_id": str(case_version_id),
            "option_code": committed_choice,
            "composite_proportionality_score": 0.88,
            "outcome": "PASSED_PROPORTIONATE",
            "suitability_score": 0.90,
            "necessity_least_intrusive_score": 0.85,
            "strict_proportionality_score": 0.89,
            "summary": "Müdahale amaca uygun ve en hafif araçla sınırlandırılmıştır.",
        },
        "vulnerable_groups_shield": {
            "case_version_id": str(case_version_id),
            "option_code": committed_choice,
            "overall_protection_status": "ROBUST_PROTECTION",
            "safety_net_floor_score": 0.92,
            "cohort_evaluations": [
                {
                    "cohort": "SPECIAL_NEEDS",
                    "impact_score": 0.90,
                    "assessment": "Öncelikli koruma güvencesi sağlanmıştır.",
                }
            ],
        },
        "counter_argument": {
            "refutation_id": "ref-1",
            "source_argument_id": "arg-A",
            "target_argument_id": "arg-B",
            "refutation_type": "PREMISE_CHALLENGE",
            "refutation_strength": 0.78,
            "rebuttal_thesis": "Kuralın istisnası kuralı zayıflatmaz, adaleti pekiştirir.",
        },
        "expert_testimony": {
            "testimony_id": "test-1",
            "source_name": "Kamu Etiği Araştırmaları Enstitüsü",
            "archetype": "ETHICS_SCHOLAR",
            "conflict_of_interest_score": 0.02,
            "epistemic_authority_tier": "TIER_1_PEER_REVIEWED",
            "testimony_statement": "Sınırlı kaynak dağıtımında orantılılık ilkesi temel normdur.",
        },
        "rights_conflict": {
            "case_version_id": str(case_version_id),
            "option_code": committed_choice,
            "collision_type": "INDIVIDUAL_LIBERTY_VS_PUBLIC_HEALTH",
            "severity": "PERMISSIBLE_RESTRICTION",
            "inalienable_core_score": 0.91,
            "constitutional_rationale": "Temel hakların özüne dokunulmaksızın kamu yararı gözetilmiştir.",
        },
        "blind_variants": {
            "case_version_id": str(case_version_id),
            "blind_mode": "ACTOR_BLIND",
            "blinded_prompt": "Özne kimliği gizlenerek yalnızca temel etik ilkeler üzerinden değerlendirilmiştir.",
            "real_identity_revealed": "Kamu Görevlisi & Vatandaş",
            "neutrality_score": 0.88,
        },
        "principle_first": {
            "case_version_id": str(case_version_id),
            "primary_principle": "PROCEDURAL_JUSTICE",
            "secondary_principle": "EMPATHY_COMPASSION",
            "consistency_score": 0.84,
            "reflection_prompt": "Seçtiğiniz ilke ile gerekçeniz arasında yüksek tutarlılık gözlendi.",
        },
        "role_flip": {
            "case_version_id": str(case_version_id),
            "initial_role": "Kuralı Uygulayan Memur",
            "flipped_role": "Sıradaki Vatandaş",
            "flipped_scenario_prompt": "Acil durumdaki vatandaşın yerine geçseydiniz kararın adil olduğunu düşünür müydünüz?",
            "perspective_shift_score": 0.72,
        },
        "decision_receipt": {
            "receipt_id": receipt.receipt_id,
            "case_version_id": str(case_version_id),
            "committed_choice": committed_choice,
            "integrity_digest": receipt.integrity_digest,
            "timestamp_utc": receipt.timestamp_utc,
        },
        "fatigue_guard": {
            "session_id": str(session_id),
            "consecutive_weigh_count": 3,
            "session_duration_minutes": 8.5,
            "pacing_status": "OPTIMAL_PACING",
            "gentle_recommendation_prompt": "Zihinsel ritminiz dengeli ve odaklanmış durumda.",
        },
        "signal_half_life": {
            "case_version_id": str(case_version_id),
            "total_half_life_days": 30,
            "elapsed_days": 6.0,
            "remaining_weight": 0.87,
            "freshness_state": "FRESH",
        },
        "verified_institution_response": {
            "case_version_id": str(case_version_id),
            "institution_name": "Ulaştırma ve Altyapı Denetleme Kurulu",
            "institution_type": "OFFICIAL_GOVERNMENT",
            "official_statement": "Koltuk tahsis ölçütleri ve kamu yararı ilkeleri resmi tebliğ ile uyumludur.",
            "verification_fingerprint": "sha256-inst-resp-9f8a32",
            "responded_at_utc": ts_str,
        },
        "source_diversity": SourceDiversityCalculator.calculate(
            case_version_id,
            [
                SourcePluralityCategory.ACADEMIC_SCIENTIFIC,
                SourcePluralityCategory.OFFICIAL_GOVERNMENT,
                SourcePluralityCategory.CIVIC_INDEPENDENT,
                SourcePluralityCategory.MAINSTREAM_JOURNALISM,
            ],
        ).to_dict(),
    }
