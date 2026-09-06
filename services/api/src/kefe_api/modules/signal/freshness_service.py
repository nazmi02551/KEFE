from __future__ import annotations

import math
from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.signal.freshness_models import (
    SignalFreshnessState,
    SignalFreshnessTier,
)

DEFAULT_HALF_LIFE_DAYS = 30


class SignalFreshnessEngine:
    @staticmethod
    def calculate_freshness(
        *,
        signal_id: UUID,
        case_version_id: UUID,
        latest_activity_at: datetime,
        as_of: datetime | None = None,
        half_life_days: int = DEFAULT_HALF_LIFE_DAYS,
    ) -> SignalFreshnessState:
        now = as_of or datetime.now(UTC)
        elapsed_seconds = max(0.0, (now - latest_activity_at).total_seconds())
        elapsed_days = elapsed_seconds / 86400.0

        decay_constant = math.log(2) / max(1, half_life_days)
        freshness_score = round(math.exp(-decay_constant * elapsed_days), 4)

        if freshness_score >= 0.85:
            tier = SignalFreshnessTier.FRESH
        elif freshness_score >= 0.50:
            tier = SignalFreshnessTier.STABLE
        elif freshness_score >= 0.20:
            tier = SignalFreshnessTier.DECAYING
        else:
            tier = SignalFreshnessTier.ARCHIVED

        return SignalFreshnessState(
            signal_id=signal_id,
            case_version_id=case_version_id,
            latest_activity_at=latest_activity_at,
            half_life_days=half_life_days,
            freshness_score=freshness_score,
            freshness_tier=tier,
        )
