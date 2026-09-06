from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.signal.freshness_models import (
    SignalFreshnessState,
    SignalFreshnessTier,
)
from kefe_api.modules.signal.freshness_service import SignalFreshnessEngine


def test_signal_freshness_engine_calculates_tiers() -> None:
    now = datetime.now(UTC)
    signal_id = uuid4()
    case_id = uuid4()

    # 1. Immediate activity -> FRESH (score ~ 1.0)
    fresh_state = SignalFreshnessEngine.calculate_freshness(
        signal_id=signal_id,
        case_version_id=case_id,
        latest_activity_at=now,
        as_of=now,
        half_life_days=30,
    )
    assert fresh_state.freshness_tier == SignalFreshnessTier.FRESH
    assert fresh_state.freshness_score == 1.0

    # 2. Exactly 30 days elapsed -> STABLE (score = 0.5)
    stable_state = SignalFreshnessEngine.calculate_freshness(
        signal_id=signal_id,
        case_version_id=case_id,
        latest_activity_at=now - timedelta(days=30),
        as_of=now,
        half_life_days=30,
    )
    assert stable_state.freshness_tier == SignalFreshnessTier.STABLE
    assert stable_state.freshness_score == 0.50

    # 3. 60 days elapsed (2 half-lives) -> DECAYING (score = 0.25)
    decaying_state = SignalFreshnessEngine.calculate_freshness(
        signal_id=signal_id,
        case_version_id=case_id,
        latest_activity_at=now - timedelta(days=60),
        as_of=now,
        half_life_days=30,
    )
    assert decaying_state.freshness_tier == SignalFreshnessTier.DECAYING
    assert decaying_state.freshness_score == 0.25

    # 4. 120 days elapsed (4 half-lives) -> ARCHIVED (score = 0.0625)
    archived_state = SignalFreshnessEngine.calculate_freshness(
        signal_id=signal_id,
        case_version_id=case_id,
        latest_activity_at=now - timedelta(days=120),
        as_of=now,
        half_life_days=30,
    )
    assert archived_state.freshness_tier == SignalFreshnessTier.ARCHIVED
    assert archived_state.freshness_score < 0.20
