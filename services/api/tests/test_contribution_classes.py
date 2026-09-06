from datetime import UTC, datetime
from uuid import UUID

from kefe_api.modules.signal.contribution_classes import (
    ContributionClassesService,
    ContributionClassId,
    IsolationAuditStatus,
)


def test_contribution_classes_service_evaluation() -> None:
    case_version_id = UUID("22222222-2222-4222-8222-222222222222")

    report = ContributionClassesService.evaluate(
        case_version_id=case_version_id,
        core_count=1000,
        exposed_count=300,
        advocacy_count=200,
        certified_at=datetime(2026, 8, 20, 10, 0, 0, tzinfo=UTC),
    )

    assert report.total_contributions == 1500
    assert len(report.classes) == 3
    assert report.contamination_risk_index == 0.0
    assert report.isolation_audit_status == IsolationAuditStatus.ENFORCED
    assert len(report.isolation_proof_hash) == 64

    class_map = {c.class_id: c for c in report.classes}

    core = class_map[ContributionClassId.CORE_PRE_RESULT]
    assert core.count == 1000
    assert core.percentage == round((1000 / 1500) * 100.0, 2)
    assert core.is_signal_eligible is True

    exposed = class_map[ContributionClassId.EXPOSED]
    assert exposed.count == 300
    assert exposed.percentage == round((300 / 1500) * 100.0, 2)
    assert exposed.is_signal_eligible is False

    advocacy = class_map[ContributionClassId.ADVOCACY_SUPPORT]
    assert advocacy.count == 200
    assert advocacy.percentage == round((200 / 1500) * 100.0, 2)
    assert advocacy.is_signal_eligible is False
