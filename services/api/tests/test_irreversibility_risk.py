from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.irreversibility_risk import (
    IrreversibilityRiskCalculator,
    IrreversibilityRiskResult,
    ReversibilityClass,
)


def test_irreversibility_risk_evaluates_classes_and_precaution() -> None:
    case_id = uuid4()

    # 1. Permanently Irreversible
    r1 = IrreversibilityRiskCalculator.evaluate(
        case_version_id=case_id,
        option_code="OPT_HYDRO_DAM",
        unwind_time_months=120,
        unwind_cost_factor=0.90,
        is_permanent_physical_damage=True,
        risk_summary="Doğal vadi ekosistemi sular altında kalıp kalıcı olarak yok olacak.",
    )
    assert isinstance(r1, IrreversibilityRiskResult)
    assert r1.reversibility_class == ReversibilityClass.PERMANENTLY_IRREVERSIBLE
    assert r1.precautionary_risk_score == 1.00

    # 2. Fully Reversible
    r2 = IrreversibilityRiskCalculator.evaluate(
        case_version_id=case_id,
        option_code="OPT_PILOT_SPEED_LIMIT",
        unwind_time_months=1,
        unwind_cost_factor=0.10,
        is_permanent_physical_damage=False,
        risk_summary="Tabela ve dijital hız radarı ayarı 1 günde geri alınabilir.",
    )
    assert r2.reversibility_class == ReversibilityClass.FULLY_REVERSIBLE
    assert r2.precautionary_risk_score < 0.20


def test_irreversibility_risk_invalid_cost() -> None:
    case_id = uuid4()
    failed = False
    try:
        IrreversibilityRiskCalculator.evaluate(
            case_version_id=case_id,
            option_code="OPT_ERR",
            unwind_time_months=5,
            unwind_cost_factor=1.5,  # > 1.0
            risk_summary="Hata",
        )
    except ValueError:
        failed = True

    assert failed is True
