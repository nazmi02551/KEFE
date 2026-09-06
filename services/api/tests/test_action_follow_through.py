from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.impact.action_models import ActionMilestone, ActionStatus
from kefe_api.modules.impact.action_service import ActionFollowThroughService


def test_propose_and_update_action_progress() -> None:
    service = ActionFollowThroughService()
    case_version_id = uuid4()

    action = service.propose_action(
        case_version_id=case_version_id,
        title="Toplu Taşıma Gece Seferleri Düzenlemesi",
        description="Belediye meclisine resmi dilekçe verilmesi ve tarife komisyonu toplantısının izlenmesi.",
        target_completion_date=datetime.now(UTC) + timedelta(days=30),
    )

    assert isinstance(action, ActionMilestone)
    assert action.status == ActionStatus.PROPOSED
    assert action.progress_percentage == 0

    updated = service.update_progress(
        case_version_id=case_version_id,
        action_id=action.action_id,
        progress_percentage=75,
        status=ActionStatus.IN_PROGRESS,
        evidence_summary="Dilekçe kabul edildi, komisyon gündemine alındı.",
        evidence_url="https://belediye.gov.tr/kararlar/2026-44",
    )

    assert updated.status == ActionStatus.IN_PROGRESS
    assert updated.progress_percentage == 75
    assert updated.evidence_url == "https://belediye.gov.tr/kararlar/2026-44"

    all_actions = service.list_actions(case_version_id)
    assert len(all_actions) == 1
    assert all_actions[0].progress_percentage == 75


def test_invalid_progress_percentage_rejected() -> None:
    service = ActionFollowThroughService()
    case_version_id = uuid4()

    action = service.propose_action(
        case_version_id=case_version_id,
        title="Eylem Başlığı",
        description="Açıklama metni yeterince uzun.",
    )

    failed = False
    try:
        service.update_progress(
            case_version_id=case_version_id,
            action_id=action.action_id,
            progress_percentage=150,  # Invalid
            status=ActionStatus.IN_PROGRESS,
        )
    except ValueError:
        failed = True

    assert failed is True
