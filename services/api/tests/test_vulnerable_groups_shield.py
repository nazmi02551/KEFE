from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.vulnerable_groups_shield import (
    CohortEvaluationItem,
    ProtectionStatus,
    VulnerableCohort,
    VulnerableGroupsShieldCalculator,
    VulnerableGroupsShieldResult,
)


def test_vulnerable_groups_shield_applies_maximin_rule() -> None:
    case_id = uuid4()

    # 1. Severe disproportionate burden on disabled / low income
    r1 = VulnerableGroupsShieldCalculator.audit(
        case_version_id=case_id,
        option_code="OPT_DIGITAL_ONLY_BUS",
        cohort_evaluations=[
            CohortEvaluationItem(
                cohort=VulnerableCohort.PERSONS_WITH_DISABILITIES,
                impact_score=-0.70,
                assessment="Akıllı telefonu veya dijital bankacılığı olmayan engelliler toplu taşımaya erişememektedir.",
            ),
            CohortEvaluationItem(
                cohort=VulnerableCohort.ELDERLY_GERIATRIC,
                impact_score=-0.60,
                assessment="Yaşlı nüfusun bilet alma bariyeri yükselmektedir.",
            ),
            CohortEvaluationItem(
                cohort=VulnerableCohort.CHILDREN_YOUTH,
                impact_score=0.40,
                assessment="Gençler için hızlı QR geçişi.",
            ),
        ],
    )
    assert isinstance(r1, VulnerableGroupsShieldResult)
    assert r1.overall_protection_status == ProtectionStatus.SEVERE_DISPROPORTIONATE_BURDEN
    assert r1.safety_net_floor_score < 0.30

    # 2. Strong protective floor
    r2 = VulnerableGroupsShieldCalculator.audit(
        case_version_id=case_id,
        option_code="OPT_UNIVERSAL_ACCESSIBLE",
        cohort_evaluations=[
            CohortEvaluationItem(
                cohort=VulnerableCohort.PERSONS_WITH_DISABILITIES,
                impact_score=0.80,
                assessment="Tüm araçlarda sesli/görsel anons ve rampa entegrasyonu.",
            ),
            CohortEvaluationItem(
                cohort=VulnerableCohort.LOW_INCOME_IMPOVERISHED,
                impact_score=0.60,
                assessment="Düşük gelirli ailelere ücretsiz ulaşım desteği.",
            ),
        ],
    )
    assert r2.overall_protection_status == ProtectionStatus.STRONG_PROTECTIVE_FLOOR


def test_vulnerable_groups_invalid_score() -> None:
    case_id = uuid4()
    failed = False
    try:
        VulnerableGroupsShieldCalculator.audit(
            case_version_id=case_id,
            option_code="OPT_ERR",
            cohort_evaluations=[
                CohortEvaluationItem(
                    cohort=VulnerableCohort.CHILDREN_YOUTH,
                    impact_score=2.0,  # > 1.0
                    assessment="Hata",
                )
            ],
        )
    except ValueError:
        failed = True

    assert failed is True
