from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ArgumentStrengthTier(StrEnum):
    TIER_A_ROBUST = "TIER_A_ROBUST"
    TIER_B_PLAUSIBLE = "TIER_B_PLAUSIBLE"
    TIER_C_WEAK_RHETORICAL = "TIER_C_WEAK_RHETORICAL"


@dataclass(frozen=True, slots=True)
class ArgumentStrengthResult:
    argument_id: UUID
    empirical_foundation_score: float
    logical_consistency_score: float
    representative_balance_score: float
    composite_strength_score: float
    strength_tier: ArgumentStrengthTier


class ArgumentStrengthEvaluator:
    @staticmethod
    def evaluate(
        *,
        argument_id: UUID,
        empirical_foundation_score: float,
        logical_consistency_score: float,
        representative_balance_score: float,
    ) -> ArgumentStrengthResult:
        for name, val in [
            ("empirical_foundation_score", empirical_foundation_score),
            ("logical_consistency_score", logical_consistency_score),
            ("representative_balance_score", representative_balance_score),
        ]:
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"{name} must be between 0.0 and 1.0, got {val}")

        # Weights: 40% empirical, 40% logic, 20% balance
        composite = round(
            (empirical_foundation_score * 0.40)
            + (logical_consistency_score * 0.40)
            + (representative_balance_score * 0.20),
            2,
        )

        if composite >= 0.80:
            tier = ArgumentStrengthTier.TIER_A_ROBUST
        elif composite >= 0.50:
            tier = ArgumentStrengthTier.TIER_B_PLAUSIBLE
        else:
            tier = ArgumentStrengthTier.TIER_C_WEAK_RHETORICAL

        return ArgumentStrengthResult(
            argument_id=argument_id,
            empirical_foundation_score=round(empirical_foundation_score, 2),
            logical_consistency_score=round(logical_consistency_score, 2),
            representative_balance_score=round(representative_balance_score, 2),
            composite_strength_score=composite,
            strength_tier=tier,
        )
