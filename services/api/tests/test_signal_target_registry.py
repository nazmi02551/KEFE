from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.impact.signal_target_registry import (
    DispatchStatus,
    SignalTargetRegistryService,
    TargetType,
)


def test_signal_target_registry_evaluation() -> None:
    signal_id = UUID("77777777-7777-4777-8777-777777777701")
    case_version_id = UUID("22222222-2222-4222-8222-222222222222")

    report = SignalTargetRegistryService.evaluate(
        signal_id=signal_id,
        case_version_id=case_version_id,
        certified_at=datetime(2026, 8, 20, 10, 0, 0, tzinfo=UTC),
    )

    assert report.signal_id == signal_id
    assert report.case_version_id == case_version_id
    assert len(report.targets) == 2
    assert report.primary_target_id == report.targets[0].target_id

    primary = report.targets[0]
    assert primary.target_type == TargetType.MUNICIPAL_GOVERNMENT
    assert primary.dispatch_status == DispatchStatus.ACKNOWLEDGED
    assert primary.response_due_days == 30
    assert primary.acknowledged_at is not None
    assert "UKOME" in primary.target_name

    secondary = report.targets[1]
    assert secondary.target_type == TargetType.MINISTRY_DEPARTMENT
    assert secondary.dispatch_status == DispatchStatus.DISPATCHED
    assert secondary.acknowledged_at is None

    assert len(report.registry_proof_hash) == 64


def test_signal_target_types_and_statuses() -> None:
    assert TargetType.MUNICIPAL_GOVERNMENT.value == "MUNICIPAL_GOVERNMENT"
    assert TargetType.REGULATORY_BODY.value == "REGULATORY_BODY"
    assert DispatchStatus.DISPATCHED.value == "DISPATCHED"
    assert DispatchStatus.ACTION_PLEDGED.value == "ACTION_PLEDGED"
