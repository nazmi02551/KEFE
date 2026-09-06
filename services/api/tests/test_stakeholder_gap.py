from __future__ import annotations

from kefe_api.modules.decision.stakeholder_gap import (
    MIN_STAKEHOLDER_SAMPLE_SIZE,
    StakeholderGapCalculator,
    StakeholderSegmentGap,
    StakeholderSegmentKey,
)


def test_stakeholder_gap_calculator_computes_points_difference() -> None:
    overall = {"A": 0.55, "B": 0.45}
    segment = {"A": 0.70, "B": 0.30}

    gap = StakeholderGapCalculator.calculate_gap(
        overall_distributions=overall,
        segment_distributions=segment,
        sample_size=150,
        segment_key=StakeholderSegmentKey.DIRECTLY_AFFECTED,
        target_option="A",
    )

    assert isinstance(gap, StakeholderSegmentGap)
    assert gap.segment_key == StakeholderSegmentKey.DIRECTLY_AFFECTED
    assert gap.gap_points == 15
    assert gap.sample_size == 150


def test_stakeholder_gap_rejects_below_minimum_privacy_threshold() -> None:
    overall = {"A": 0.55, "B": 0.45}
    segment = {"A": 0.70, "B": 0.30}

    failed = False
    try:
        StakeholderGapCalculator.calculate_gap(
            overall_distributions=overall,
            segment_distributions=segment,
            sample_size=20,  # Below threshold 30
            segment_key=StakeholderSegmentKey.GENERAL_PUBLIC,
            target_option="A",
        )
    except ValueError as exc:
        failed = True
        assert "below minimum privacy threshold" in str(exc) or "Cannot disclose" in str(exc)

    assert failed is True
