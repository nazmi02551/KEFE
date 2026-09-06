from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.deliberation_depth import (
    DeliberationDepthCalculator,
    DeliberationDepthResult,
    DepthLevel,
)


def test_deliberation_depth_evaluates_profound() -> None:
    case_id = uuid4()

    r = DeliberationDepthCalculator.calculate(
        case_version_id=case_id,
        arguments_inspected_count=8,
        evidence_items_verified_count=4,
        counter_views_explored_count=3,
    )

    assert isinstance(r, DeliberationDepthResult)
    assert r.depth_level == DepthLevel.PROFOUND_DELIBERATION
    assert r.deliberation_depth_score == 1.0


def test_deliberation_depth_superficial() -> None:
    case_id = uuid4()

    r = DeliberationDepthCalculator.calculate(
        case_version_id=case_id,
        arguments_inspected_count=1,
        evidence_items_verified_count=0,
        counter_views_explored_count=0,
    )

    assert r.depth_level == DepthLevel.SUPERFICIAL_SKIMMING


def test_deliberation_depth_invalid_counts() -> None:
    case_id = uuid4()
    failed = False
    try:
        DeliberationDepthCalculator.calculate(
            case_version_id=case_id,
            arguments_inspected_count=-1,  # < 0
            evidence_items_verified_count=0,
            counter_views_explored_count=0,
        )
    except ValueError:
        failed = True

    assert failed is True
