from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.proportionality_test import (
    ProportionalityCalculator,
    ProportionalityOutcome,
    ProportionalityTestResult,
)


def test_proportionality_calculator_evaluates_three_prongs() -> None:
    case_id = uuid4()

    # 1. Proportional Valid
    r1 = ProportionalityCalculator.evaluate(
        case_version_id=case_id,
        option_code="OPT_TARGETED_AUDIT",
        suitability_score=0.85,
        necessity_least_intrusive_score=0.90,
        strict_proportionality_score=0.80,
        summary="Risk odaklı hedefli denetim, tüm vatandaşları izlemeden kamu yararını sağlamaktadır.",
    )
    assert isinstance(r1, ProportionalityTestResult)
    assert r1.outcome == ProportionalityOutcome.PROPORTIONAL_VALID
    assert r1.composite_proportionality_score > 0.80

    # 2. Disproportionate Invalid
    r2 = ProportionalityCalculator.evaluate(
        case_version_id=case_id,
        option_code="OPT_BLANKET_BAN",
        suitability_score=0.50,
        necessity_least_intrusive_score=0.20,
        strict_proportionality_score=0.25,
        summary="Toptan yasaklama ölçülülük ilkesine aykırıdır; daha hafif alternatifler mevcuttur.",
    )
    assert r2.outcome == ProportionalityOutcome.DISPROPORTIONATE_INVALID


def test_proportionality_invalid_scores() -> None:
    case_id = uuid4()
    failed = False
    try:
        ProportionalityCalculator.evaluate(
            case_version_id=case_id,
            option_code="OPT_ERR",
            suitability_score=1.5,  # > 1.0
            necessity_least_intrusive_score=0.5,
            strict_proportionality_score=0.5,
            summary="Açıklama",
        )
    except ValueError:
        failed = True

    assert failed is True
