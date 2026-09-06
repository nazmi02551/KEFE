from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.signal.signal_qualification import (
    SignalQualificationService,
    SignalQualificationStatus,
    SignalQualificationTier,
)


def test_signal_qualification_gold_standard() -> None:
    signal_id = UUID("77777777-7777-4777-8777-777777777701")
    case_version_id = UUID("22222222-2222-4222-8222-222222222222")

    report = SignalQualificationService.evaluate(
        signal_id=signal_id,
        case_version_id=case_version_id,
        case_title="Son koltuk kime verilmeli?",
        sample_size=1200,
        entropy_score=0.85,
        deliberation_depth_score=0.88,
        astroturfing_immunity_score=0.96,
        pre_result_ratio=1.0,
        certified_at=datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC),
    )

    assert report.qualification_status == SignalQualificationStatus.QUALIFIED
    assert report.qualification_tier == SignalQualificationTier.GOLD_STANDARD
    assert report.overall_score >= 0.85
    assert len(report.criteria) == 5
    assert all(c.is_passed for c in report.criteria)
    assert len(report.eligible_channels) == 4
    assert "POLICY_DELIBERATION_REPORT" in report.eligible_channels
    assert len(report.qualification_audit_hash) == 64


def test_signal_qualification_silver_validated() -> None:
    signal_id = UUID("77777777-7777-4777-8777-777777777702")
    case_version_id = UUID("22222222-2222-4222-8222-222222222223")

    report = SignalQualificationService.evaluate(
        signal_id=signal_id,
        case_version_id=case_version_id,
        case_title="Test Case",
        sample_size=350,
        entropy_score=0.75,
        deliberation_depth_score=0.70,
        astroturfing_immunity_score=0.90,
        pre_result_ratio=0.98,
        certified_at=datetime(2026, 8, 20, 10, 0, 0, tzinfo=UTC),
    )

    assert report.qualification_status == SignalQualificationStatus.QUALIFIED
    assert report.qualification_tier == SignalQualificationTier.SILVER_VALIDATED
    assert len(report.eligible_channels) == 3
    assert "POLICY_DELIBERATION_REPORT" not in report.eligible_channels


def test_signal_qualification_bronze_observed() -> None:
    signal_id = UUID("77777777-7777-4777-8777-777777777703")
    case_version_id = UUID("22222222-2222-4222-8222-222222222224")

    report = SignalQualificationService.evaluate(
        signal_id=signal_id,
        case_version_id=case_version_id,
        case_title="Bronze Case",
        sample_size=120,
        entropy_score=0.70,
        deliberation_depth_score=0.65,
        astroturfing_immunity_score=0.85,
        pre_result_ratio=0.96,
        certified_at=datetime(2026, 8, 22, 10, 0, 0, tzinfo=UTC),
    )

    assert report.qualification_status == SignalQualificationStatus.QUALIFIED
    assert report.qualification_tier == SignalQualificationTier.BRONZE_OBSERVED
    assert len(report.eligible_channels) == 1
    assert report.eligible_channels[0] == "CIVIC_PUBLIC_DASHBOARD"


def test_signal_qualification_provisional_sample() -> None:
    signal_id = UUID("77777777-7777-4777-8777-777777777704")
    case_version_id = UUID("22222222-2222-4222-8222-222222222225")

    report = SignalQualificationService.evaluate(
        signal_id=signal_id,
        case_version_id=case_version_id,
        case_title="Small Sample Case",
        sample_size=65,
        entropy_score=0.80,
        deliberation_depth_score=0.75,
        astroturfing_immunity_score=0.92,
        pre_result_ratio=1.0,
    )

    assert report.qualification_status == SignalQualificationStatus.PROVISIONAL
    assert report.qualification_tier == SignalQualificationTier.UNQUALIFIED
    assert len(report.eligible_channels) == 0


def test_signal_qualification_disqualified_astroturfing() -> None:
    signal_id = UUID("77777777-7777-4777-8777-777777777705")
    case_version_id = UUID("22222222-2222-4222-8222-222222222226")

    report = SignalQualificationService.evaluate(
        signal_id=signal_id,
        case_version_id=case_version_id,
        case_title="Bot Infiltrated Case",
        sample_size=600,
        entropy_score=0.40,
        deliberation_depth_score=0.45,
        astroturfing_immunity_score=0.35,  # fails bot gate
        pre_result_ratio=0.90,
    )

    assert report.qualification_status == SignalQualificationStatus.DISQUALIFIED
    assert report.qualification_tier == SignalQualificationTier.UNQUALIFIED
    assert len(report.eligible_channels) == 0
