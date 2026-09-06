from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.normative_models import (
    CaseNormativeModelResult,
    NormativeModelsCalculator,
    NormativePhilosophy,
    OptionNormativeEvaluation,
)


def test_normative_models_evaluates_four_frameworks() -> None:
    case_id = uuid4()

    # Option A: Utilitarian dominant (0.90)
    opt_a = NormativeModelsCalculator.evaluate_option(
        option_code="OPT_A",
        utilitarian_score=0.90,
        deontological_score=0.30,
        rawlsian_score=0.50,
        virtue_score=0.40,
    )
    assert isinstance(opt_a, OptionNormativeEvaluation)
    assert opt_a.dominant_philosophy == NormativePhilosophy.UTILITARIAN_MAX_WELFARE

    # Option B: Rawlsian dominant (0.85)
    opt_b = NormativeModelsCalculator.evaluate_option(
        option_code="OPT_B",
        utilitarian_score=0.40,
        deontological_score=0.60,
        rawlsian_score=0.85,
        virtue_score=0.50,
    )
    assert opt_b.dominant_philosophy == NormativePhilosophy.RAWLSIAN_MAXIMIN_EQUITY

    case_res = NormativeModelsCalculator.evaluate_case(case_id, [opt_a, opt_b])
    assert isinstance(case_res, CaseNormativeModelResult)
    assert len(case_res.evaluations) == 2


def test_normative_models_invalid_score_range() -> None:
    failed = False
    try:
        NormativeModelsCalculator.evaluate_option(
            option_code="OPT_ERR",
            utilitarian_score=1.5,  # > 1.0
            deontological_score=0.5,
            rawlsian_score=0.5,
            virtue_score=0.5,
        )
    except ValueError:
        failed = True

    assert failed is True
