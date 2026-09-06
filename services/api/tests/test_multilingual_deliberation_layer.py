from __future__ import annotations

from kefe_api.modules.decision.multilingual_deliberation_layer import (
    MultilingualDeliberationLayerService,
    MultilingualTranslationResult,
    TranslationFidelityTier,
)


def test_multilingual_translates_high_fidelity() -> None:
    r = MultilingualDeliberationLayerService.translate_argument(
        translation_id="tra_001",
        source_locale="tr",
        target_locale="en",
        translated_text="Algorithmic transparency is an essential precondition for civic legitimacy.",
        semantic_similarity_score=0.96,
    )

    assert isinstance(r, MultilingualTranslationResult)
    assert r.fidelity_tier == TranslationFidelityTier.HIGH_FIDELITY_CERTIFIED
    assert r.source_locale == "tr"
    assert r.target_locale == "en"
    assert r.semantic_similarity_score == 0.96


def test_multilingual_invalid_locale() -> None:
    failed = False
    try:
        MultilingualDeliberationLayerService.translate_argument(
            translation_id="tra_002",
            source_locale="t",  # < 2
            target_locale="e",  # < 2
            translated_text="Kı",  # < 3
            semantic_similarity_score=1.50,  # > 1.0
        )
    except ValueError:
        failed = True

    assert failed is True
