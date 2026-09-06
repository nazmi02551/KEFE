from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import math
from uuid import UUID


class FreshnessState(StrEnum):
    FRESH = "FRESH"
    STABLE = "STABLE"
    DEPRECATING = "DEPRECATING"
    EXPIRED_NEEDS_RETEST = "EXPIRED_NEEDS_RETEST"


@dataclass(frozen=True, slots=True)
class SignalHalfLifeResult:
    signal_id: str
    case_version_id: UUID
    half_life_days: int
    age_days: float
    remaining_weight: float
    freshness_state: FreshnessState


class SignalHalfLifeCalculator:
    @staticmethod
    def evaluate(
        *,
        signal_id: str,
        case_version_id: UUID,
        half_life_days: int,
        age_days: float,
    ) -> SignalHalfLifeResult:
        if half_life_days <= 0:
            raise ValueError("half_life_days must be positive")
        if age_days < 0.0:
            raise ValueError("age_days cannot be negative")
        if len(signal_id.strip()) < 4:
            raise ValueError("signal_id must have at least 4 characters")

        decay_rate = math.log(2) / half_life_days
        remaining_weight = math.exp(-decay_rate * age_days)
        remaining_weight = max(0.0, min(1.0, remaining_weight))

        if remaining_weight >= 0.85:
            state = FreshnessState.FRESH
        elif remaining_weight >= 0.50:
            state = FreshnessState.STABLE
        elif remaining_weight >= 0.20:
            state = FreshnessState.DEPRECATING
        else:
            state = FreshnessState.EXPIRED_NEEDS_RETEST

        return SignalHalfLifeResult(
            signal_id=signal_id.strip(),
            case_version_id=case_version_id,
            half_life_days=half_life_days,
            age_days=round(age_days, 1),
            remaining_weight=round(remaining_weight, 3),
            freshness_state=state,
        )
