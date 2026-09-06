from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class SignalFreshnessTier(StrEnum):
    FRESH = "FRESH"
    STABLE = "STABLE"
    DECAYING = "DECAYING"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class SignalFreshnessState:
    signal_id: UUID
    case_version_id: UUID
    latest_activity_at: datetime
    half_life_days: int
    freshness_score: float
    freshness_tier: SignalFreshnessTier
