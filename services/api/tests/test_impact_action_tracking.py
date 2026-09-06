from __future__ import annotations

from kefe_api.modules.decision.impact_action_tracking import (
    ImpactActionResult,
    ImpactActionTracker,
    MilestoneStatus,
)


def test_impact_action_tracker_evaluates_progress() -> None:
    r = ImpactActionTracker.evaluate(
        action_id="act_001",
        institution_name="İBB Çevre Koruma Dairesi",
        pledge_title="Marmara Kıyı Şeridi Atık Filtreleme İstasyonu İnşası",
        milestone_status=MilestoneStatus.IN_PROGRESS,
        completion_percentage=65,
        target_completion_utc="2026-12-31T00:00:00Z",
    )

    assert isinstance(r, ImpactActionResult)
    assert r.completion_percentage == 65
    assert r.milestone_status == MilestoneStatus.IN_PROGRESS


def test_impact_action_tracker_invalid_percentage() -> None:
    failed = False
    try:
        ImpactActionTracker.evaluate(
            action_id="act_002",
            institution_name="Kurum",
            pledge_title="Taahhüt Başlığı",
            milestone_status=MilestoneStatus.PROMISED,
            completion_percentage=150,  # > 100
            target_completion_utc="2026-12-31T00:00:00Z",
        )
    except ValueError:
        failed = True

    assert failed is True
