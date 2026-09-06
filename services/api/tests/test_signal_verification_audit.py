from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from kefe_api.modules.signal.audit_models import (
    SignalAuditEvent,
    SignalAuditEventType,
)
from kefe_api.modules.signal.audit_service import SignalAuditService


def test_signal_audit_trail_chains_hashes_and_verifies_integrity() -> None:
    service = SignalAuditService()
    signal_id = uuid4()
    case_id = uuid4()

    # Event 1: Threshold crossed
    e1 = service.append_audit_event(
        signal_id=signal_id,
        case_version_id=case_id,
        event_type=SignalAuditEventType.THRESHOLD_CROSSED,
        actor_ref="system.signal_aggregator",
        evidence_snapshot={"sample_size": 2500, "agreement_rate": 0.82, "stability": 0.94},
    )

    assert e1.previous_hash is None
    assert len(e1.entry_hash) == 64

    # Event 2: Editorial certified
    e2 = service.append_audit_event(
        signal_id=signal_id,
        case_version_id=case_id,
        event_type=SignalAuditEventType.EDITORIAL_CERTIFIED,
        actor_ref="auditor:editorial_board_01",
        evidence_snapshot={"certification_status": "APPROVED", "reviewed_at": datetime.now(UTC).isoformat()},
    )

    assert e2.previous_hash == e1.entry_hash
    assert len(e2.entry_hash) == 64

    # Event 3: Metric refreshed
    e3 = service.append_audit_event(
        signal_id=signal_id,
        case_version_id=case_id,
        event_type=SignalAuditEventType.METRIC_REFRESHED,
        actor_ref="system.daily_job",
        evidence_snapshot={"freshness_score": 0.98},
    )

    assert e3.previous_hash == e2.entry_hash

    trail = service.get_audit_trail(signal_id)
    assert len(trail) == 3
    assert service.verify_chain_integrity(signal_id) is True
