from __future__ import annotations

from kefe_api.modules.decision.privacy_budget_monitor import (
    PrivacyBudgetMonitorService,
    PrivacyBudgetResult,
    PrivacyBudgetState,
)


def test_privacy_budget_evaluates_healthy() -> None:
    r = PrivacyBudgetMonitorService.evaluate_budget(
        monitor_id="pbm_001",
        total_epsilon_budget=1.0,
        consumed_epsilon=0.25,
        delta_parameter=1e-5,
        queries_executed_count=120,
    )

    assert isinstance(r, PrivacyBudgetResult)
    assert r.budget_state == PrivacyBudgetState.BUDGET_HEALTHY_AMPLE
    assert r.consumed_epsilon == 0.25
    assert r.queries_executed_count == 120


def test_privacy_budget_invalid_delta() -> None:
    failed = False
    try:
        PrivacyBudgetMonitorService.evaluate_budget(
            monitor_id="pbm_002",
            total_epsilon_budget=-1.0,  # <= 0
            consumed_epsilon=0.5,
            delta_parameter=0.05,  # > 0.01
            queries_executed_count=-5,  # < 0
        )
    except ValueError:
        failed = True

    assert failed is True
