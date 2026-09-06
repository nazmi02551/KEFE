from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.divergence_anatomy import (
    DivergenceAnatomyCalculator,
    DivergenceAnatomyResult,
    DivergenceDriverType,
)


def test_divergence_anatomy_calculator_determines_primary_driver_and_shares() -> None:
    case_id = uuid4()
    inputs = [
        {
            "driver_type": "NORMATIVE_VALUE_WEIGHT",
            "weight": 55.0,
            "explanation": "Özgürlük vs güvenlik önceliklendirmesi.",
        },
        {
            "driver_type": "FACTUAL_PROBABILITY_ASSESSMENT",
            "weight": 25.0,
            "explanation": "Risk gerçekleşme ihtimali tahminleri.",
        },
        {
            "driver_type": "PROCEDURAL_GOVERNANCE",
            "weight": 20.0,
            "explanation": "Denetimin kim tarafından yapılacağı.",
        },
    ]

    result = DivergenceAnatomyCalculator.calculate(case_id, inputs)

    assert isinstance(result, DivergenceAnatomyResult)
    assert result.primary_driver == DivergenceDriverType.NORMATIVE_VALUE_WEIGHT
    assert len(result.drivers) == 3

    assert result.drivers[0].share_percentage == 55.0
    assert result.drivers[1].share_percentage == 25.0
    assert result.drivers[2].share_percentage == 20.0
