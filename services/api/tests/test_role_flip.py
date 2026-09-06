from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.role_flip import (
    RoleFlipCalculator,
    RoleFlipResult,
)


def test_role_flip_calculator_evaluates_shift() -> None:
    case_id = uuid4()

    r = RoleFlipCalculator.evaluate(
        case_version_id=case_id,
        initial_role="Tesis Sahibi / Sanayici",
        flipped_role="Bölge Sakini / Temiz Su Tüketicisi",
        flipped_scenario_prompt="Şimdi fabrikanın atık boşalttığı nehir kıyısında yaşayan ve tarım yapan bir köylü olduğunuzu hayal edin.",
        perspective_shift_score=0.74,
    )

    assert isinstance(r, RoleFlipResult)
    assert r.initial_role == "Tesis Sahibi / Sanayici"
    assert r.perspective_shift_score == 0.74


def test_role_flip_invalid_score() -> None:
    case_id = uuid4()
    failed = False
    try:
        RoleFlipCalculator.evaluate(
            case_version_id=case_id,
            initial_role="A",
            flipped_role="B",
            flipped_scenario_prompt="Kısa",
            perspective_shift_score=1.2,
        )
    except ValueError:
        failed = True

    assert failed is True
