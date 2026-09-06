from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.signal.signal_versioning import (
    SignalVersioningService,
)


def test_signal_versioning_evaluation() -> None:
    signal_id = UUID("77777777-7777-4777-8777-777777777701")
    case_version_id = UUID("22222222-2222-4222-8222-222222222222")

    report = SignalVersioningService.evaluate(
        signal_id=signal_id,
        case_version_id=case_version_id,
        certified_at=datetime(2026, 8, 20, 12, 0, 0, tzinfo=UTC),
    )

    assert report.signal_id == signal_id
    assert report.case_version_id == case_version_id
    assert report.current_version == "v1.2.0-entropy"
    assert len(report.current_methodology_hash) == 64
    assert len(report.snapshots) == 2

    s1, s2 = report.snapshots
    assert s1.methodology_version == "v1.0.0"
    assert s1.parent_snapshot_hash is None
    assert len(s1.snapshot_hash) == 64

    assert s2.methodology_version == "v1.2.0-entropy"
    assert s2.parent_snapshot_hash == s1.snapshot_hash
    assert len(s2.snapshot_hash) == 64

    assert report.audit_chain_valid is True
    assert report.latest_delta is not None
    assert report.latest_delta.from_version == "v1.0.0"
    assert report.latest_delta.to_version == "v1.2.0-entropy"
    assert report.latest_delta.distribution_shift == 0.02


def test_signal_versioning_hash_determinism() -> None:
    time_ref = datetime(2026, 8, 1, 10, 0, 0, tzinfo=UTC)
    h1 = SignalVersioningService.compute_snapshot_hash(
        parent_hash=None,
        methodology_version="v1.0.0",
        sample_size=500,
        confidence_score=0.90,
        distribution={"A": 0.6, "B": 0.4},
        calculated_at=time_ref,
    )
    h2 = SignalVersioningService.compute_snapshot_hash(
        parent_hash=None,
        methodology_version="v1.0.0",
        sample_size=500,
        confidence_score=0.90,
        distribution={"B": 0.4, "A": 0.6},
        calculated_at=time_ref,
    )
    assert h1 == h2
    assert len(h1) == 64
