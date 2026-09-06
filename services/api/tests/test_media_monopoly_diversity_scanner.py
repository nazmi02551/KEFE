from __future__ import annotations

from kefe_api.modules.decision.media_monopoly_diversity_scanner import (
    MediaDiversityResult,
    MediaMonopolyDiversityScannerService,
    MediaPluralismLevel,
)


def test_media_scanner_evaluates_pluralism() -> None:
    r = MediaMonopolyDiversityScannerService.scan_topic(
        scanner_id="med_001",
        topic_cluster="İklim Değişikliği ve Yenilenebilir Enerji Düzenlemeleri",
        source_diversity_index=0.88,
        independent_outlets_count=12,
    )

    assert isinstance(r, MediaDiversityResult)
    assert r.pluralism_level == MediaPluralismLevel.PLURALISTIC_INDEPENDENT_DIVERSE
    assert r.source_diversity_index == 0.88
    assert r.independent_outlets_count == 12


def test_media_scanner_invalid_inputs() -> None:
    failed = False
    try:
        MediaMonopolyDiversityScannerService.scan_topic(
            scanner_id="med_002",
            topic_cluster="Kıs",  # < 4
            source_diversity_index=-0.1,  # < 0.0
            independent_outlets_count=-1,  # < 0
        )
    except ValueError:
        failed = True

    assert failed is True
