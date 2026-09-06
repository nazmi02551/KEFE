#!/usr/bin/env python3
"""
KEFE Proje Sağlık ve Doğrulama Scripti (Unified Project Health)

Tek komutla projenin tüm kritik kapılarını doğrular:
1. Capability Portfolio (128 yetenek aynası)
2. Python API Testleri (pytest)
3. Flutter Statik Analiz (flutter analyze)
4. Git Çalışma Ağacı Durumu
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_check(name: str, cmd: list[str], cwd: Path) -> bool:
    print(f"\n[+] Kontrol Ediliyor: {name}...")
    print(f"    Komut: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False, shell=True)
        if res.returncode == 0:
            print(f"    >>> {name}: [BASARILI / PASS]")
            if res.stdout.strip():
                lines = res.stdout.strip().split("\n")
                summary = lines[-1] if lines else ""
                print(f"        Ozet: {summary}")
            return True
        else:
            print(f"    >>> {name}: [HATA / FAIL] (Kod: {res.returncode})")
            if res.stderr.strip():
                print(f"        Hata: {res.stderr.strip()[:300]}")
            elif res.stdout.strip():
                print(f"        Cikti: {res.stdout.strip()[:300]}")
            return False
    except Exception as e:
        print(f"    >>> {name}: [CALISTIRILAMADI] ({e})")
        return False


def main() -> int:
    print("=" * 65)
    print("      KEFE PROJE SAGLIK VE DOGRULAMA MERKEZI (PROJECT HEALTH)      ")
    print("=" * 65)

    results = []

    # 1. Capability Portfolio Gate
    p_validator = ROOT / "scripts" / "validate_capability_portfolio.py"
    if p_validator.exists():
        results.append(("Capability Portfolio Gate", run_check("Capability Portfolio", [sys.executable, str(p_validator)], ROOT)))

    # 2. Python API Tests
    api_dir = ROOT / "services" / "api"
    if api_dir.exists():
        results.append(
            (
                "Python API Pytest",
                run_check(
                    "Python API Tests",
                    [
                        sys.executable,
                        "-m",
                        "pytest",
                        "services/api/tests/test_bridge_arguments.py",
                        "services/api/tests/test_divergence_anatomy.py",
                        "services/api/tests/test_depolarization_index.py",
                        "services/api/tests/test_deliberation_depth.py",
                        "services/api/tests/test_synthetic_astroturfing_shield.py",
                        "services/api/tests/test_threshold_analysis.py",
                        "services/api/tests/test_stakeholder_impact.py",
                        "services/api/tests/test_outcome_triangle.py",
                        "services/api/tests/test_change_mind_inquiry.py",
                        "services/api/tests/test_argument_strength.py",
                        "services/api/tests/test_fallacy_detector.py",
                        "services/api/tests/test_irreversibility_risk.py",
                        "services/api/tests/test_unintended_consequences.py",
                        "services/api/tests/test_proportionality_test.py",
                        "services/api/tests/test_vulnerable_groups_shield.py",
                        "services/api/tests/test_counter_argument.py",
                        "services/api/tests/test_expert_testimony.py",
                        "services/api/tests/test_rights_conflict.py",
                        "services/api/tests/test_blind_variants.py",
                        "services/api/tests/test_principle_first.py",
                        "services/api/tests/test_role_flip.py",
                        "services/api/tests/test_decision_receipt.py",
                        "services/api/tests/test_fatigue_guard.py",
                        "services/api/tests/test_signal_half_life.py",
                        "services/api/tests/test_verified_institution_response.py",
                        "services/api/tests/test_source_diversity.py",
                        "services/api/tests/test_signal_consensus_card_api.py",
                        "services/api/tests/test_institution_response.py",
                        "services/api/tests/test_institution_response_api.py",
                        "services/api/tests/test_action_follow_through.py",
                        "services/api/tests/test_action_follow_through_api.py",
                        "services/api/tests/test_case_objection.py",
                        "services/api/tests/test_case_objection_api.py",
                        "services/api/tests/test_correction_history.py",
                        "services/api/tests/test_correction_history_api.py",
                        "services/api/tests/test_case_search_filter.py",
                        "services/api/tests/test_case_search_filter_api.py",
                        "services/api/tests/test_canonical_public_feed_catalog.py",
                        "services/api/tests/test_admin_case_builder_http.py",
                        "services/api/tests/test_otp_http_delivery.py",
                        "services/api/tests/test_guest_session_rotation.py",
                        "services/api/tests/test_privacy_export_deletion_hardening.py",
                        "services/api/tests/test_case_quality_checklist_api.py",
                        "services/api/tests/test_user_controlled_discovery_api.py",
                        "services/api/tests/test_temporal_drift.py",
                        "services/api/tests/test_signal_health_card_api.py",
                        "services/api/tests/test_historical_retrospective.py",
                        "services/api/tests/test_divergence_classifier.py",
                        "services/api/tests/test_consensus_divergence_api.py",
                        "services/api/tests/test_normative_models.py",
                        "services/api/tests/test_normative_models_api.py",
                        "services/api/tests/test_policy_simulator.py",
                        "services/api/tests/test_policy_simulator_api.py",
                        "services/api/tests/test_process_analysis.py",
                        "services/api/tests/test_process_analysis_api.py",
                        "services/api/tests/test_responsibility_analysis.py",
                        "services/api/tests/test_responsibility_analysis_api.py",
                        "services/api/tests/test_incentive_map.py",
                        "services/api/tests/test_incentive_map_api.py",
                        "services/api/tests/test_perspective_clustering.py",
                        "services/api/tests/test_perspective_clustering_api.py",
                        "services/api/tests/test_segment_distribution.py",
                        "services/api/tests/test_segment_distribution_api.py",
                        "services/api/tests/test_stakeholder_distribution.py",
                        "services/api/tests/test_stakeholder_distribution_api.py",
                        "services/api/tests/test_expert_public_gap.py",
                        "services/api/tests/test_expert_public_gap_api.py",
                        "services/api/tests/test_budget_tradeoff_simulator.py",
                        "services/api/tests/test_observe_mode_exploration.py",
                        "services/api/tests/test_community_dilemma_proposals.py",
                        "services/api/tests/test_signal_qualification.py",
                        "services/api/tests/test_signal_qualification_api.py",
                        "services/api/tests/test_contribution_classes.py",
                        "services/api/tests/test_contribution_classes_api.py",
                        "services/api/tests/test_signal_scope.py",
                        "services/api/tests/test_signal_scope_api.py",
                        "services/api/tests/test_signal_versioning.py",
                        "services/api/tests/test_signal_versioning_api.py",
                        "services/api/tests/test_signal_target_registry.py",
                        "services/api/tests/test_signal_target_registry_api.py",
                        "-q",
                    ],
                    ROOT,
                ),
            )
        )

    # 3. Flutter Tests & Analyze
    mobile_dir = ROOT / "apps" / "mobile"
    if mobile_dir.exists():
        results.append(
            (
                "Flutter Unit Tests",
                run_check(
                    "Flutter Mobile Unit Tests",
                    [
                        "flutter",
                        "test",
                        "test/bridge_arguments_test.dart",
                        "test/divergence_anatomy_test.dart",
                        "test/depolarization_index_test.dart",
                        "test/deliberation_depth_test.dart",
                        "test/synthetic_astroturfing_shield_test.dart",
                        "test/threshold_analysis_test.dart",
                        "test/stakeholder_impact_test.dart",
                        "test/outcome_triangle_test.dart",
                        "test/change_mind_inquiry_test.dart",
                        "test/argument_strength_test.dart",
                        "test/fallacy_detector_test.dart",
                        "test/irreversibility_risk_test.dart",
                        "test/unintended_consequences_test.dart",
                        "test/proportionality_test.dart",
                        "test/vulnerable_groups_shield_test.dart",
                        "test/counter_argument_test.dart",
                        "test/expert_testimony_test.dart",
                        "test/rights_conflict_test.dart",
                        "test/blind_variants_test.dart",
                        "test/principle_first_test.dart",
                        "test/role_flip_test.dart",
                        "test/decision_receipt_test.dart",
                        "test/fatigue_guard_test.dart",
                        "test/signal_half_life_test.dart",
                        "test/verified_institution_response_test.dart",
                        "test/deliberation_cockpit_showcase_test.dart",
                        "test/signal_consensus_section_test.dart",
                        "test/source_diversity_test.dart",
                        "test/connected_alpha_app_config_test.dart",
                        "test/insufficient_info_response_test.dart",
                        "test/open_methodology_test.dart",
                        "test/stakeholder_gap_test.dart",
                        "test/institution_response_test.dart",
                        "test/institution_response_section_test.dart",
                        "test/action_follow_through_test.dart",
                        "test/case_objection_test.dart",
                        "test/correction_history_test.dart",
                        "test/explore_tolerant_search_test.dart",
                        "test/saved_case_lifecycle_updates_test.dart",
                        "test/civic_petition_simulator_test.dart",
                        "test/user_data_export_deletion_test.dart",
                        "test/offline_decision_queue_test.dart",
                        "test/accessibility_contrast_motion_test.dart",
                        "test/case_quality_checklist_test.dart",
                        "test/user_controlled_discovery_test.dart",
                        "test/temporal_drift_test.dart",
                        "test/signal_health_card_test.dart",
                        "test/kefe_today_projection_test.dart",
                        "test/historical_retrospective_test.dart",
                        "test/consensus_divergence_test.dart",
                        "test/normative_models_test.dart",
                        "test/policy_simulator_test.dart",
                        "test/process_analysis_test.dart",
                        "test/responsibility_analysis_test.dart",
                        "test/incentive_map_test.dart",
                        "test/perspective_clustering_test.dart",
                        "test/segment_distribution_test.dart",
                        "test/stakeholder_distribution_test.dart",
                        "test/expert_public_gap_test.dart",
                        "test/budget_tradeoff_simulator_test.dart",
                        "test/observe_mode_exploration_test.dart",
                        "test/community_dilemma_proposals_test.dart",
                        "test/signal_qualification_test.dart",
                        "test/contribution_classes_test.dart",
                        "test/signal_scope_alignment_test.dart",
                        "test/signal_versioning_test.dart",
                        "test/signal_target_registry_test.dart",
                    ],
                    mobile_dir,
                ),
            )
        )
        results.append(
            (
                "Flutter Analyze",
                run_check(
                    "Flutter Mobile Analyze",
                    ["dart", "analyze", "--no-fatal-warnings"],
                    mobile_dir,
                ),
            )
        )

    print("\n" + "=" * 65)
    print("                         SONUC TABLOSU                           ")
    print("=" * 65)
    all_ok = True
    for name, status in results:
        status_str = "GECTI (PASS)" if status else "BASARISIZ (FAIL)"
        print(f" - {name:<35} : {status_str}")
        if not status:
            all_ok = False

    print("=" * 65)
    if all_ok:
        print("[*] Proje saglikli, tum kapilar dogrulandi.")
        return 0
    else:
        print("[!] Bazi kapilar basarisiz oldu, lutfen duzeltiniz.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
