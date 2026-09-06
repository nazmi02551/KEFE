from __future__ import annotations

import pytest
from kefe_api.modules.decision.segment_distribution import (
    MIN_SEGMENT_SAMPLE_SIZE,
    PrivacySafeSegmentDistributionService,
    SegmentCohortType,
)


def test_segment_distribution_suppresses_below_privacy_threshold():
    cohort = PrivacySafeSegmentDistributionService.evaluate_cohort(
        cohort_type=SegmentCohortType.AGE_COHORT,
        cohort_label="Genç Kuşak (Küçük Grup)",
        sample_size=15,  # below 30
        raw_shares={"A": 0.8, "B": 0.2},
    )

    assert cohort.is_suppressed is True
    assert cohort.suppression_reason == "INSUFFICIENT_SAMPLE_PRIVACY_THRESHOLD"
    assert cohort.option_shares == {}
    assert cohort.primary_choice is None
    assert cohort.entropy_score == 0.0


def test_segment_distribution_evaluates_valid_cohort_above_threshold():
    cohort = PrivacySafeSegmentDistributionService.evaluate_cohort(
        cohort_type=SegmentCohortType.URBAN_RURAL_COHORT,
        cohort_label="Metropol Alanı",
        sample_size=150,  # well above 30
        raw_shares={"A": 0.6, "B": 0.4},
    )

    assert cohort.is_suppressed is False
    assert cohort.suppression_reason is None
    assert cohort.sample_size == 150
    assert cohort.primary_choice == "A"
    assert sum(cohort.option_shares.values()) == pytest.approx(1.0, rel=1e-2)
    assert 0.0 < cohort.entropy_score <= 1.0


def test_entropy_calculation_boundary_conditions():
    # Empty shares
    assert PrivacySafeSegmentDistributionService.calculate_entropy({}) == 0.0
    # Single option (zero entropy)
    assert PrivacySafeSegmentDistributionService.calculate_entropy({"A": 1.0}) == 0.0
    # Equal split (maximum entropy = 1.0)
    assert PrivacySafeSegmentDistributionService.calculate_entropy({"A": 0.5, "B": 0.5}) == 1.0


def test_get_segment_distribution_contract_guarantees():
    result = PrivacySafeSegmentDistributionService.get_segment_distribution("case-v1-uuid")

    assert result.case_version_id == "case-v1-uuid"
    assert result.minimum_sample_threshold == MIN_SEGMENT_SAMPLE_SIZE
    assert result.minimum_sample_threshold == 30
    assert result.overall_sample_size > 0
    assert len(result.segments) > 0

    # Verify privacy guarantees
    assert result.privacy_guarantees.k_anonymity_threshold == 30
    assert result.privacy_guarantees.no_individual_profiling is True
    assert result.privacy_guarantees.differential_privacy_noise_applied is True

    # Check that at least one suppressed segment exists in the test/demo set
    suppressed_segments = [s for s in result.segments if s.is_suppressed]
    assert len(suppressed_segments) >= 1
    for s in suppressed_segments:
        assert s.sample_size < MIN_SEGMENT_SAMPLE_SIZE
        assert s.option_shares == {}
