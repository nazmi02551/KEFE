from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class StandingTier(StrEnum):
    EXEMPLARY_CONTRIBUTOR = "EXEMPLARY_CONTRIBUTOR"
    ESTABLISHED_PARTICIPANT = "ESTABLISHED_PARTICIPANT"
    ACTIVE_EXPLORER = "ACTIVE_EXPLORER"
    RESTRICTED_OR_PROBATIONARY = "RESTRICTED_OR_PROBATIONARY"


@dataclass(frozen=True, slots=True)
class CommunityTrustStandingResult:
    user_pseudonym_id: str
    trust_score: float
    standing_tier: StandingTier
    bridge_argument_count: int
    verified_weigh_count: int
    infraction_count: int


class CommunityTrustCalculator:
    @staticmethod
    def calculate_standing(
        *,
        user_pseudonym_id: str,
        bridge_argument_count: int,
        verified_weigh_count: int,
        infraction_count: int,
    ) -> CommunityTrustStandingResult:
        if bridge_argument_count < 0:
            raise ValueError("bridge_argument_count cannot be negative")
        if verified_weigh_count < 0:
            raise ValueError("verified_weigh_count cannot be negative")
        if infraction_count < 0:
            raise ValueError("infraction_count cannot be negative")
        if len(user_pseudonym_id.strip()) < 4:
            raise ValueError("user_pseudonym_id must have at least 4 characters")

        # Base score starts at 0.50
        score = 0.50
        score += min(0.30, bridge_argument_count * 0.05)
        score += min(0.20, verified_weigh_count * 0.01)
        score -= infraction_count * 0.25

        score = max(0.0, min(1.0, score))

        if infraction_count >= 2 or score < 0.30:
            tier = StandingTier.RESTRICTED_OR_PROBATIONARY
        elif score >= 0.85:
            tier = StandingTier.EXEMPLARY_CONTRIBUTOR
        elif score >= 0.65:
            tier = StandingTier.ESTABLISHED_PARTICIPANT
        else:
            tier = StandingTier.ACTIVE_EXPLORER

        return CommunityTrustStandingResult(
            user_pseudonym_id=user_pseudonym_id.strip(),
            trust_score=round(score, 2),
            standing_tier=tier,
            bridge_argument_count=bridge_argument_count,
            verified_weigh_count=verified_weigh_count,
            infraction_count=infraction_count,
        )
