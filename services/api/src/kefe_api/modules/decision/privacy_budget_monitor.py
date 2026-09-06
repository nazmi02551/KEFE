from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PrivacyBudgetState(StrEnum):
    BUDGET_HEALTHY_AMPLE = "BUDGET_HEALTHY_AMPLE"
    BUDGET_APPROACHING_LIMIT = "BUDGET_APPROACHING_LIMIT"
    BUDGET_EXHAUSTED_THROTTLED = "BUDGET_EXHAUSTED_THROTTLED"


@dataclass(frozen=True, slots=True)
class PrivacyBudgetResult:
    monitor_id: str
    total_epsilon_budget: float
    consumed_epsilon: float
    delta_parameter: float
    budget_state: PrivacyBudgetState
    queries_executed_count: int


class PrivacyBudgetMonitorService:
    @staticmethod
    def evaluate_budget(
        *,
        monitor_id: str,
        total_epsilon_budget: float,
        consumed_epsilon: float,
        delta_parameter: float = 1e-5,
        queries_executed_count: int = 0,
    ) -> PrivacyBudgetResult:
        if total_epsilon_budget <= 0.0:
            raise ValueError(f"total_epsilon_budget must be > 0.0, got {total_epsilon_budget}")
        if consumed_epsilon < 0.0:
            raise ValueError(f"consumed_epsilon cannot be negative, got {consumed_epsilon}")
        if not 0.0 <= delta_parameter <= 0.01:
            raise ValueError(f"delta_parameter must be in [0.0, 0.01], got {delta_parameter}")
        if queries_executed_count < 0:
            raise ValueError("queries_executed_count cannot be negative")

        ratio = consumed_epsilon / total_epsilon_budget
        if ratio <= 0.50:
            state = PrivacyBudgetState.BUDGET_HEALTHY_AMPLE
        elif ratio <= 0.85:
            state = PrivacyBudgetState.BUDGET_APPROACHING_LIMIT
        else:
            state = PrivacyBudgetState.BUDGET_EXHAUSTED_THROTTLED

        return PrivacyBudgetResult(
            monitor_id=monitor_id.strip(),
            total_epsilon_budget=round(total_epsilon_budget, 2),
            consumed_epsilon=round(consumed_epsilon, 2),
            delta_parameter=delta_parameter,
            budget_state=state,
            queries_executed_count=queries_executed_count,
        )
