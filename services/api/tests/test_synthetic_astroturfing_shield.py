"""Tests for SyntheticAstroturfingShieldService (CAP-073).

Covers:
- All three BotDefenseState transitions and boundary conditions
- Input validation (score/index out of range, negative count)
- Output immutability and field precision
- BotShieldResult identity and equality
- Edge values at state-classification thresholds
- cluster_id / target_case_id whitespace stripping
- Analytical snapshot bot_shield block shape (via build_analytical_perspectives)
"""
from __future__ import annotations

import uuid

import pytest

from kefe_api.modules.decision.analytical_snapshots import build_analytical_perspectives
from kefe_api.modules.decision.synthetic_astroturfing_shield import (
    BotDefenseState,
    BotShieldResult,
    SyntheticAstroturfingShieldService,
)

_inspect = SyntheticAstroturfingShieldService.inspect_cluster


# ---------------------------------------------------------------------------
# State: ISOLATED_QUARANTINE_SWARM
# ---------------------------------------------------------------------------

def test_isolated_quarantine_swarm_nominal() -> None:
    r = _inspect(
        cluster_id="bot_cls_001",
        target_case_id="case_ai_001",
        synthetic_probability_score=0.94,
        quarantined_bot_payloads_count=1450,
        semantic_entropy_index=0.12,
    )
    assert r.defense_state == BotDefenseState.ISOLATED_QUARANTINE_SWARM
    assert r.quarantined_bot_payloads_count == 1450
    assert r.synthetic_probability_score == 0.94
    assert r.semantic_entropy_index == 0.12


def test_isolated_quarantine_swarm_at_lower_boundary() -> None:
    # Exact thresholds: score=0.80, entropy<0.25
    r = _inspect(
        cluster_id="c",
        target_case_id="t",
        synthetic_probability_score=0.80,
        quarantined_bot_payloads_count=0,
        semantic_entropy_index=0.24,
    )
    assert r.defense_state == BotDefenseState.ISOLATED_QUARANTINE_SWARM


def test_not_quarantine_if_entropy_at_0_25() -> None:
    # entropy == 0.25 means < 0.25 is False → SUSPECTED, not QUARANTINE
    r = _inspect(
        cluster_id="c",
        target_case_id="t",
        synthetic_probability_score=0.85,
        quarantined_bot_payloads_count=0,
        semantic_entropy_index=0.25,
    )
    assert r.defense_state == BotDefenseState.SUSPECTED_BOT_COORDINATION


# ---------------------------------------------------------------------------
# State: SUSPECTED_BOT_COORDINATION
# ---------------------------------------------------------------------------

def test_suspected_coordination_nominal() -> None:
    r = _inspect(
        cluster_id="sus_cls",
        target_case_id="case_b",
        synthetic_probability_score=0.55,
        quarantined_bot_payloads_count=12,
        semantic_entropy_index=0.50,
    )
    assert r.defense_state == BotDefenseState.SUSPECTED_BOT_COORDINATION


def test_suspected_at_lower_boundary() -> None:
    # Exact lower boundary for SUSPECTED: score == 0.40
    r = _inspect(
        cluster_id="c",
        target_case_id="t",
        synthetic_probability_score=0.40,
        quarantined_bot_payloads_count=0,
        semantic_entropy_index=0.80,
    )
    assert r.defense_state == BotDefenseState.SUSPECTED_BOT_COORDINATION


def test_not_suspected_just_below_0_40() -> None:
    r = _inspect(
        cluster_id="c",
        target_case_id="t",
        synthetic_probability_score=0.39,
        quarantined_bot_payloads_count=0,
        semantic_entropy_index=0.90,
    )
    assert r.defense_state == BotDefenseState.ORGANIC_CITIZEN_AUTHENTIC


# ---------------------------------------------------------------------------
# State: ORGANIC_CITIZEN_AUTHENTIC
# ---------------------------------------------------------------------------

def test_organic_citizen_authentic_nominal() -> None:
    r = _inspect(
        cluster_id="org_cls",
        target_case_id="case_c",
        synthetic_probability_score=0.05,
        quarantined_bot_payloads_count=0,
        semantic_entropy_index=0.95,
    )
    assert r.defense_state == BotDefenseState.ORGANIC_CITIZEN_AUTHENTIC
    assert r.quarantined_bot_payloads_count == 0


def test_organic_at_zero_probability() -> None:
    r = _inspect(
        cluster_id="c",
        target_case_id="t",
        synthetic_probability_score=0.0,
        quarantined_bot_payloads_count=0,
        semantic_entropy_index=1.0,
    )
    assert r.defense_state == BotDefenseState.ORGANIC_CITIZEN_AUTHENTIC


# ---------------------------------------------------------------------------
# Output precision and immutability
# ---------------------------------------------------------------------------

def test_scores_rounded_to_two_decimals() -> None:
    r = _inspect(
        cluster_id="c",
        target_case_id="t",
        synthetic_probability_score=0.8456789,
        quarantined_bot_payloads_count=1,
        semantic_entropy_index=0.12345,
    )
    # round() with 2 decimals
    assert r.synthetic_probability_score == round(0.8456789, 2)
    assert r.semantic_entropy_index == round(0.12345, 2)


def test_result_is_frozen_dataclass() -> None:
    r = _inspect(
        cluster_id="c",
        target_case_id="t",
        synthetic_probability_score=0.1,
        quarantined_bot_payloads_count=0,
        semantic_entropy_index=0.9,
    )
    with pytest.raises((AttributeError, TypeError)):
        r.defense_state = BotDefenseState.SUSPECTED_BOT_COORDINATION  # type: ignore[misc]


def test_cluster_and_case_id_whitespace_stripped() -> None:
    r = _inspect(
        cluster_id="  cls_001  ",
        target_case_id="  case_001  ",
        synthetic_probability_score=0.1,
        quarantined_bot_payloads_count=0,
        semantic_entropy_index=0.9,
    )
    assert r.cluster_id == "cls_001"
    assert r.target_case_id == "case_001"


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("score", [-0.01, 1.01, 2.0, -1.0])
def test_invalid_synthetic_probability_score(score: float) -> None:
    with pytest.raises(ValueError, match="synthetic_probability_score"):
        _inspect(
            cluster_id="c",
            target_case_id="t",
            synthetic_probability_score=score,
            quarantined_bot_payloads_count=0,
            semantic_entropy_index=0.5,
        )


@pytest.mark.parametrize("entropy", [-0.01, 1.01, 2.5])
def test_invalid_semantic_entropy_index(entropy: float) -> None:
    with pytest.raises(ValueError, match="semantic_entropy_index"):
        _inspect(
            cluster_id="c",
            target_case_id="t",
            synthetic_probability_score=0.5,
            quarantined_bot_payloads_count=0,
            semantic_entropy_index=entropy,
        )


def test_negative_quarantined_count_raises() -> None:
    with pytest.raises(ValueError, match="quarantined_bot_payloads_count"):
        _inspect(
            cluster_id="c",
            target_case_id="t",
            synthetic_probability_score=0.5,
            quarantined_bot_payloads_count=-1,
            semantic_entropy_index=0.5,
        )


# ---------------------------------------------------------------------------
# BotDefenseState enum completeness
# ---------------------------------------------------------------------------

def test_all_three_states_reachable() -> None:
    states = set()
    for score, entropy in [(0.05, 0.9), (0.50, 0.5), (0.85, 0.10)]:
        r = _inspect(
            cluster_id="c",
            target_case_id="t",
            synthetic_probability_score=score,
            quarantined_bot_payloads_count=0,
            semantic_entropy_index=entropy,
        )
        states.add(r.defense_state)
    assert states == {
        BotDefenseState.ORGANIC_CITIZEN_AUTHENTIC,
        BotDefenseState.SUSPECTED_BOT_COORDINATION,
        BotDefenseState.ISOLATED_QUARANTINE_SWARM,
    }


# ---------------------------------------------------------------------------
# Analytical snapshot integration — bot_shield block shape (CAP-073)
# ---------------------------------------------------------------------------

def test_analytical_snapshot_bot_shield_block_shape() -> None:
    """build_analytical_perspectives must include a well-formed bot_shield block."""
    case_version_id = uuid.uuid4()
    session_id = uuid.uuid4()
    actor_id = uuid.uuid4()

    perspectives = build_analytical_perspectives(
        case_version_id=case_version_id,
        session_id=session_id,
        actor_id=actor_id,
        committed_choice="A",
    )
    assert "bot_shield" in perspectives, "bot_shield key missing from analytical perspectives"

    shield = perspectives["bot_shield"]
    # Required fields per CAP-073 analytical snapshot contract
    assert "anomaly_score" in shield
    assert "sybil_risk_tier" in shield
    assert "synthetic_patterns_detected" in shield
    assert "integrity_status" in shield
    assert "quarantined_bot_payloads_count" in shield
    assert "semantic_entropy_index" in shield

    # Integrity status must be a non-blank string
    assert isinstance(shield["integrity_status"], str) and shield["integrity_status"]

    # Numeric bounds
    assert 0.0 <= shield["anomaly_score"] <= 1.0
    assert 0.0 <= shield["semantic_entropy_index"] <= 1.0
    assert shield["quarantined_bot_payloads_count"] >= 0

    # sybil_risk_tier must be a non-blank string
    assert isinstance(shield["sybil_risk_tier"], str) and shield["sybil_risk_tier"]

    # synthetic_patterns_detected must be boolean
    assert isinstance(shield["synthetic_patterns_detected"], bool)