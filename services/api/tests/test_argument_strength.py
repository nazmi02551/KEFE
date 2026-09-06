from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.argument_strength import (
    ArgumentStrengthEvaluator,
    ArgumentStrengthResult,
    ArgumentStrengthTier,
)


def test_argument_strength_evaluates_tiers() -> None:
    arg_id = uuid4()

    # 1. Tier A Robust (0.9, 0.9, 0.8 => 0.88)
    r1 = ArgumentStrengthEvaluator.evaluate(
        argument_id=arg_id,
        empirical_foundation_score=0.90,
        logical_consistency_score=0.90,
        representative_balance_score=0.80,
    )
    assert isinstance(r1, ArgumentStrengthResult)
    assert r1.strength_tier == ArgumentStrengthTier.TIER_A_ROBUST
    assert r1.composite_strength_score >= 0.80

    # 2. Tier C Weak (0.2, 0.3, 0.2 => 0.24)
    r2 = ArgumentStrengthEvaluator.evaluate(
        argument_id=arg_id,
        empirical_foundation_score=0.20,
        logical_consistency_score=0.30,
        representative_balance_score=0.20,
    )
    assert r2.strength_tier == ArgumentStrengthTier.TIER_C_WEAK_RHETORICAL


def test_argument_strength_out_of_bounds() -> None:
    arg_id = uuid4()
    failed = False
    try:
        ArgumentStrengthEvaluator.evaluate(
            argument_id=arg_id,
            empirical_foundation_score=1.2,  # > 1.0
            logical_consistency_score=0.5,
            representative_balance_score=0.5,
        )
    except ValueError:
        failed = True

    assert failed is True
