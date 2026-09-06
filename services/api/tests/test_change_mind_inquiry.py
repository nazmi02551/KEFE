from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.change_mind_inquiry import (
    ChangeMindInquiryCalculator,
    ChangeMindInquiryResult,
    CounterfactualConditionType,
    EpistemicFlexibilityClass,
    SelectedCounterfactualCondition,
)


def test_change_mind_inquiry_evaluates_openness_and_absolutism() -> None:
    case_id = uuid4()

    # 1. Epistemically Open (multiple counter-conditions)
    conditions_open = [
        SelectedCounterfactualCondition(
            condition_type=CounterfactualConditionType.EMPIRICAL_DATA_THRESHOLD,
            description="Kaza oranlarında %20'den fazla azalma kanıtlanırsa.",
        ),
        SelectedCounterfactualCondition(
            condition_type=CounterfactualConditionType.VULNERABILITY_PROTECTION,
            description="Engelli vatandaşların erişim hakkı garanti altına alınırsa.",
        ),
    ]
    r1 = ChangeMindInquiryCalculator.evaluate(case_id, conditions_open)
    assert isinstance(r1, ChangeMindInquiryResult)
    assert r1.flexibility_class == EpistemicFlexibilityClass.HIGHLY_EPISTEMIC_OPEN
    assert len(r1.selected_conditions) == 2

    # 2. Categorical Absolute (unconditional stance only)
    conditions_abs = [
        SelectedCounterfactualCondition(
            condition_type=CounterfactualConditionType.UNCONDITIONAL_STANCE,
            description="Bu konu temel bir haktır, hiçbir koşulda pazarlık konusu yapılamaz.",
        )
    ]
    r2 = ChangeMindInquiryCalculator.evaluate(case_id, conditions_abs)
    assert r2.flexibility_class == EpistemicFlexibilityClass.CATEGORICAL_ABSOLUTE


def test_change_mind_inquiry_empty_conditions_rejected() -> None:
    case_id = uuid4()
    failed = False
    try:
        ChangeMindInquiryCalculator.evaluate(case_id, [])
    except ValueError:
        failed = True

    assert failed is True
