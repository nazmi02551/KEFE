from __future__ import annotations

from kefe_api.modules.decision.decision_tree_branching import (
    DecisionTreeBranchingService,
    DecisionTreeNodeResult,
    TreeNodeType,
)


def test_decision_tree_creates_valid_node() -> None:
    r = DecisionTreeBranchingService.create_node(
        tree_id="tree_001",
        root_case_id="case_9814",
        node_label="Yenilenebilir Enerji Teşvik Paketi",
        node_type=TreeNodeType.PRIMARY_DECISION_FORK,
        branch_probability=0.75,
        projected_impact_summary="Orta vadede karbon emisyonlarında %30 azalma ve yerel istihdamda artış öngörülmektedir.",
    )

    assert isinstance(r, DecisionTreeNodeResult)
    assert r.node_type == TreeNodeType.PRIMARY_DECISION_FORK
    assert r.branch_probability == 0.75


def test_decision_tree_invalid_probability() -> None:
    failed = False
    try:
        DecisionTreeBranchingService.create_node(
            tree_id="tree_002",
            root_case_id="case_9814",
            node_label="Kısa",  # < 5
            node_type=TreeNodeType.TERMINAL_OUTCOME_LEAF,
            branch_probability=1.50,  # > 1.0
            projected_impact_summary="Kısa",  # < 10
        )
    except ValueError:
        failed = True

    assert failed is True
