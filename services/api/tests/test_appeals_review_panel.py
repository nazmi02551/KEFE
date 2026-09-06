from __future__ import annotations

from kefe_api.modules.decision.appeals_review_panel import (
    AppealsReviewPanelService,
    AppealsReviewResult,
    AppealVerdict,
)


def test_appeals_review_panel_overturns_decision() -> None:
    r = AppealsReviewPanelService.resolve_appeal(
        appeal_id="app_001",
        target_resource_id="rsn_9814",
        panelist_count=7,
        votes_to_overturn=5,  # 5/7 = 0.71 >= 0.67
        resolution_summary="Hakem heyeti argümanın akademik bir eleştiri olduğunu ve kural ihlali oluşturmadığını oy çokluğuyla tespit etmiştir.",
    )

    assert isinstance(r, AppealsReviewResult)
    assert r.appeal_verdict == AppealVerdict.OVERTURNED_RESTORED
    assert r.panelist_count == 7
    assert r.favor_ratio == 0.71


def test_appeals_review_invalid_panelists() -> None:
    failed = False
    try:
        AppealsReviewPanelService.resolve_appeal(
            appeal_id="app_002",
            target_resource_id="rsn_9814",
            panelist_count=2,  # < 3
            votes_to_overturn=1,
            resolution_summary="Kısa gerekçe özeti.",
        )
    except ValueError:
        failed = True

    assert failed is True
