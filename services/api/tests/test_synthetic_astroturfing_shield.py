from __future__ import annotations

from kefe_api.modules.decision.synthetic_astroturfing_shield import (
    BotDefenseState,
    BotShieldResult,
    SyntheticAstroturfingShieldService,
)


def test_synthetic_shield_quarantines_swarm() -> None:
    r = SyntheticAstroturfingShieldService.inspect_cluster(
        cluster_id="bot_cls_001",
        target_case_id="case_ai_001",
        synthetic_probability_score=0.94,
        quarantined_bot_payloads_count=1450,
        semantic_entropy_index=0.12,
    )

    assert isinstance(r, BotShieldResult)
    assert r.defense_state == BotDefenseState.ISOLATED_QUARANTINE_SWARM
    assert r.quarantined_bot_payloads_count == 1450
    assert r.synthetic_probability_score == 0.94


def test_synthetic_shield_invalid_inputs() -> None:
    failed = False
    try:
        SyntheticAstroturfingShieldService.inspect_cluster(
            cluster_id="bot_002",
            target_case_id="c_002",
            synthetic_probability_score=1.50,  # > 1.0
            quarantined_bot_payloads_count=-10,  # < 0
            semantic_entropy_index=2.0,  # > 1.0
        )
    except ValueError:
        failed = True

    assert failed is True
