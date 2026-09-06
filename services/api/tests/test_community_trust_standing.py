from __future__ import annotations

from kefe_api.modules.decision.community_trust_standing import (
    CommunityTrustCalculator,
    CommunityTrustStandingResult,
    StandingTier,
)


def test_community_trust_standing_evaluates_exemplary() -> None:
    r = CommunityTrustCalculator.calculate_standing(
        user_pseudonym_id="usr_anon_914",
        bridge_argument_count=5,  # +0.25
        verified_weigh_count=20,  # +0.20
        infraction_count=0,
    )

    assert isinstance(r, CommunityTrustStandingResult)
    assert r.standing_tier == StandingTier.EXEMPLARY_CONTRIBUTOR
    assert r.trust_score == 0.95


def test_community_trust_standing_probationary() -> None:
    r = CommunityTrustCalculator.calculate_standing(
        user_pseudonym_id="usr_anon_881",
        bridge_argument_count=0,
        verified_weigh_count=5,
        infraction_count=2,  # 2 infractions
    )

    assert r.standing_tier == StandingTier.RESTRICTED_OR_PROBATIONARY


def test_community_trust_invalid_counts() -> None:
    failed = False
    try:
        CommunityTrustCalculator.calculate_standing(
            user_pseudonym_id="usr_anon_882",
            bridge_argument_count=-1,  # < 0
            verified_weigh_count=0,
            infraction_count=0,
        )
    except ValueError:
        failed = True

    assert failed is True
