from __future__ import annotations

from kefe_api.modules.decision.cross_cultural_norm_framework import (
    CrossCulturalNormFrameworkService,
    CulturalNormDimension,
    CulturalNormResult,
)


def test_cross_cultural_maps_norms() -> None:
    r = CrossCulturalNormFrameworkService.map_norms(
        framework_id="cn_001",
        region_identifier="TR-MARMARA",
        primary_dimension=CulturalNormDimension.COMMUNITY_SOLIDARITY_AND_MUTUALITY,
        cultural_alignment_score=0.92,
        universal_baseline_compliance=True,
        norm_synthesis_summary="İmece ve dayanışma geleneği ile modern şeffaflık ilkelerinin sentezi.",
    )

    assert isinstance(r, CulturalNormResult)
    assert r.primary_dimension == CulturalNormDimension.COMMUNITY_SOLIDARITY_AND_MUTUALITY
    assert r.universal_baseline_compliance is True
    assert r.cultural_alignment_score == 0.92


def test_cross_cultural_invalid_region() -> None:
    failed = False
    try:
        CrossCulturalNormFrameworkService.map_norms(
            framework_id="cn_002",
            region_identifier="T",  # < 2
            primary_dimension=CulturalNormDimension.INDIVIDUAL_AUTONOMY_AND_LIBERTY,
            cultural_alignment_score=1.20,  # > 1.0
            universal_baseline_compliance=False,
            norm_synthesis_summary="Kısa",  # < 10
        )
    except ValueError:
        failed = True

    assert failed is True
