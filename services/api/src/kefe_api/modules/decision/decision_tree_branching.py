from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TreeNodeType(StrEnum):
    PRIMARY_DECISION_FORK = "PRIMARY_DECISION_FORK"
    CONTINGENCY_BRANCH = "CONTINGENCY_BRANCH"
    TERMINAL_OUTCOME_LEAF = "TERMINAL_OUTCOME_LEAF"


@dataclass(frozen=True, slots=True)
class DecisionTreeNodeResult:
    tree_id: str
    root_case_id: str
    node_label: str
    node_type: TreeNodeType
    branch_probability: float
    projected_impact_summary: str


class DecisionTreeBranchingService:
    @staticmethod
    def create_node(
        *,
        tree_id: str,
        root_case_id: str,
        node_label: str,
        node_type: TreeNodeType,
        branch_probability: float,
        projected_impact_summary: str,
    ) -> DecisionTreeNodeResult:
        if len(node_label.strip()) < 5:
            raise ValueError("node_label must have at least 5 characters")
        if not 0.0 <= branch_probability <= 1.0:
            raise ValueError(f"branch_probability must be in [0.0, 1.0], got {branch_probability}")
        if len(projected_impact_summary.strip()) < 10:
            raise ValueError("projected_impact_summary must have at least 10 characters")

        return DecisionTreeNodeResult(
            tree_id=tree_id.strip(),
            root_case_id=root_case_id.strip(),
            node_label=node_label.strip(),
            node_type=node_type,
            branch_probability=round(branch_probability, 2),
            projected_impact_summary=projected_impact_summary.strip(),
        )
