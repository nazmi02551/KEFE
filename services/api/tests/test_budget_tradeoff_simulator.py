from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.budget_tradeoff_simulator import (
    BudgetTradeoffResult,
    BudgetTradeoffSimulator,
    TradeoffProfile,
)


def test_budget_tradeoff_evaluates_human_capital() -> None:
    case_id = uuid4()

    r = BudgetTradeoffSimulator.evaluate(
        tradeoff_id="trade_001",
        case_version_id=case_id,
        healthcare_pct=35,
        education_pct=30,
        infrastructure_pct=20,
        green_transition_pct=15,
    )

    assert isinstance(r, BudgetTradeoffResult)
    assert r.tradeoff_profile == TradeoffProfile.HEALTH_EDUCATION_PRIORITY
    assert r.unallocated_pct == 0


def test_budget_tradeoff_exceeds_100() -> None:
    case_id = uuid4()
    failed = False
    try:
        BudgetTradeoffSimulator.evaluate(
            tradeoff_id="trade_002",
            case_version_id=case_id,
            healthcare_pct=40,
            education_pct=40,
            infrastructure_pct=30,  # total = 110 > 100
            green_transition_pct=0,
        )
    except ValueError:
        failed = True

    assert failed is True
