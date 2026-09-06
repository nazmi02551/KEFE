from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class CounterfactualConditionType(StrEnum):
    EMPIRICAL_DATA_THRESHOLD = "EMPIRICAL_DATA_THRESHOLD"
    VULNERABILITY_PROTECTION = "VULNERABILITY_PROTECTION"
    ECONOMIC_SUSTAINABILITY = "ECONOMIC_SUSTAINABILITY"
    MORAL_IMPASSE_EMPATHY = "MORAL_IMPASSE_EMPATHY"
    UNCONDITIONAL_STANCE = "UNCONDITIONAL_STANCE"


class EpistemicFlexibilityClass(StrEnum):
    HIGHLY_EPISTEMIC_OPEN = "HIGHLY_EPISTEMIC_OPEN"
    CONDITIONALLY_FLEXIBLE = "CONDITIONALLY_FLEXIBLE"
    CATEGORICAL_ABSOLUTE = "CATEGORICAL_ABSOLUTE"


@dataclass(frozen=True, slots=True)
class SelectedCounterfactualCondition:
    condition_type: CounterfactualConditionType
    description: str


@dataclass(frozen=True, slots=True)
class ChangeMindInquiryResult:
    case_version_id: UUID
    selected_conditions: tuple[SelectedCounterfactualCondition, ...]
    flexibility_class: EpistemicFlexibilityClass
    custom_falsification_note: str | None = None


class ChangeMindInquiryCalculator:
    @staticmethod
    def evaluate(
        case_version_id: UUID,
        conditions: list[SelectedCounterfactualCondition],
        custom_note: str | None = None,
    ) -> ChangeMindInquiryResult:
        if not conditions:
            raise ValueError("At least one counterfactual condition or stance must be selected")

        has_unconditional = any(
            c.condition_type == CounterfactualConditionType.UNCONDITIONAL_STANCE
            for c in conditions
        )

        if has_unconditional and len(conditions) == 1:
            flex_class = EpistemicFlexibilityClass.CATEGORICAL_ABSOLUTE
        elif len(conditions) >= 2:
            flex_class = EpistemicFlexibilityClass.HIGHLY_EPISTEMIC_OPEN
        else:
            flex_class = EpistemicFlexibilityClass.CONDITIONALLY_FLEXIBLE

        return ChangeMindInquiryResult(
            case_version_id=case_version_id,
            selected_conditions=tuple(conditions),
            flexibility_class=flex_class,
            custom_falsification_note=custom_note.strip() if custom_note else None,
        )
