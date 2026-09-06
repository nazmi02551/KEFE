from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.signal.signal_scope import (
    JurisdictionLevel,
    ScopeAlignmentStatus,
    SignalScopeAlignmentService,
)


def test_signal_scope_strictly_aligned() -> None:
    signal_id = UUID("77777777-7777-4777-8777-777777777701")
    case_version_id = UUID("22222222-2222-4222-8222-222222222222")

    report = SignalScopeAlignmentService.evaluate(
        signal_id=signal_id,
        case_version_id=case_version_id,
        jurisdiction_level=JurisdictionLevel.MUNICIPAL,
        target_population="Kent İçi Raylı Sistem Yolcuları",
        geographic_scope="İstanbul / Türkiye",
        validity_window_days=90,
        jurisdiction_score=0.96,
        geographic_score=0.92,
        demographic_score=0.88,
        temporal_score=0.95,
        certified_at=datetime(2026, 8, 20, 10, 0, 0, tzinfo=UTC),
    )

    assert report.signal_id == signal_id
    assert report.case_version_id == case_version_id
    assert report.jurisdiction_level == JurisdictionLevel.MUNICIPAL
    assert report.alignment_status == ScopeAlignmentStatus.STRICTLY_ALIGNED
    assert report.overall_alignment_score >= 0.85
    assert len(report.dimensions) == 4
    assert all(d.is_valid for d in report.dimensions)
    assert len(report.scope_seal_hash) == 64


def test_signal_scope_overbroad_warning() -> None:
    signal_id = UUID("77777777-7777-4777-8777-777777777702")
    case_version_id = UUID("22222222-2222-4222-8222-222222222223")

    report = SignalScopeAlignmentService.evaluate(
        signal_id=signal_id,
        case_version_id=case_version_id,
        jurisdiction_level=JurisdictionLevel.REGIONAL,
        target_population="Marmara Bölgesi Sakinleri",
        geographic_scope="Marmara / Türkiye",
        validity_window_days=60,
        jurisdiction_score=0.78,
        geographic_score=0.72,
        demographic_score=0.74,
        temporal_score=0.75,
        certified_at=datetime(2026, 8, 20, 10, 0, 0, tzinfo=UTC),
    )

    assert report.alignment_status == ScopeAlignmentStatus.OVERBROAD_WARNING
    assert 0.70 <= report.overall_alignment_score < 0.85


def test_signal_scope_mismatch_disqualified() -> None:
    signal_id = UUID("77777777-7777-4777-8777-777777777703")
    case_version_id = UUID("22222222-2222-4222-8222-222222222224")

    report = SignalScopeAlignmentService.evaluate(
        signal_id=signal_id,
        case_version_id=case_version_id,
        jurisdiction_level=JurisdictionLevel.NATIONAL,
        target_population="Genel Seçmen Kitlesi",
        geographic_scope="Türkiye Geneli",
        validity_window_days=30,
        jurisdiction_score=0.45,
        geographic_score=0.50,
        demographic_score=0.40,
        temporal_score=0.60,
        certified_at=datetime(2026, 8, 20, 10, 0, 0, tzinfo=UTC),
    )

    assert report.alignment_status == ScopeAlignmentStatus.MISMATCH_DISQUALIFIED
    assert report.overall_alignment_score < 0.70
