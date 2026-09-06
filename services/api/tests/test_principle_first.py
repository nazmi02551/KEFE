from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.principle_first import (
    PrincipleFirstCalculator,
    PrincipleFirstResult,
    PrincipleType,
)


def test_principle_first_calculator_evaluates_consistency() -> None:
    case_id = uuid4()

    r = PrincipleFirstCalculator.evaluate(
        case_version_id=case_id,
        primary_principle=PrincipleType.INDIVIDUAL_LIBERTY,
        secondary_principle=PrincipleType.PROCEDURAL_JUSTICE,
        consistency_score=0.88,
        reflection_prompt="İlk kararınızda bireysel özgürlüğü önceliklendirdiniz; somut vakada da bu ilkeyle uyumlu kaldınız.",
    )

    assert isinstance(r, PrincipleFirstResult)
    assert r.primary_principle == PrincipleType.INDIVIDUAL_LIBERTY
    assert r.consistency_score == 0.88


def test_principle_first_invalid_score() -> None:
    case_id = uuid4()
    failed = False
    try:
        PrincipleFirstCalculator.evaluate(
            case_version_id=case_id,
            primary_principle=PrincipleType.COLLECTIVE_WELLBEING,
            secondary_principle=PrincipleType.EMPATHY_COMPASSION,
            consistency_score=-0.2,  # < 0.0
            reflection_prompt="Prompt",
        )
    except ValueError:
        failed = True

    assert failed is True
