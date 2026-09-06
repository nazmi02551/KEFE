from __future__ import annotations

from kefe_api.modules.decision.adaptive_cognitive_load import (
    AdaptiveCognitiveLoadResult,
    AdaptiveCognitiveLoadService,
    CognitiveDensityMode,
)


def test_adaptive_cognitive_load_streamlines() -> None:
    r = AdaptiveCognitiveLoadService.configure_profile(
        profile_id="cog_001",
        density_mode=CognitiveDensityMode.STREAMLINED_ESSENTIALS,
        comprehension_retention_index=0.92,
    )

    assert isinstance(r, AdaptiveCognitiveLoadResult)
    assert r.density_mode == CognitiveDensityMode.STREAMLINED_ESSENTIALS
    assert r.reading_time_reduction_pct == 0.60
    assert r.is_fatigue_mitigation_active is True
    assert r.comprehension_retention_index == 0.92


def test_adaptive_cognitive_load_invalid_index() -> None:
    failed = False
    try:
        AdaptiveCognitiveLoadService.configure_profile(
            profile_id="cog_002",
            density_mode=CognitiveDensityMode.SCHOLARLY_EXHAUSTIVE,
            comprehension_retention_index=1.50,  # > 1.0
        )
    except ValueError:
        failed = True

    assert failed is True
