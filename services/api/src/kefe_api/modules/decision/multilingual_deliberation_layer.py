from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TranslationFidelityTier(StrEnum):
    HIGH_FIDELITY_CERTIFIED = "HIGH_FIDELITY_CERTIFIED"
    COMMUNITY_VERIFIED = "COMMUNITY_VERIFIED"
    MACHINE_RAW_PREVIEW = "MACHINE_RAW_PREVIEW"


@dataclass(frozen=True, slots=True)
class MultilingualTranslationResult:
    translation_id: str
    source_locale: str
    target_locale: str
    fidelity_tier: TranslationFidelityTier
    semantic_similarity_score: float
    translated_text: str


class MultilingualDeliberationLayerService:
    @staticmethod
    def translate_argument(
        *,
        translation_id: str,
        source_locale: str,
        target_locale: str,
        translated_text: str,
        semantic_similarity_score: float = 0.95,
    ) -> MultilingualTranslationResult:
        if len(source_locale.strip()) < 2 or len(target_locale.strip()) < 2:
            raise ValueError("Locales must have at least 2 characters")
        if len(translated_text.strip()) < 3:
            raise ValueError("translated_text must have at least 3 characters")
        if not 0.0 <= semantic_similarity_score <= 1.0:
            raise ValueError(f"semantic_similarity_score must be in [0.0, 1.0], got {semantic_similarity_score}")

        if semantic_similarity_score >= 0.90:
            tier = TranslationFidelityTier.HIGH_FIDELITY_CERTIFIED
        elif semantic_similarity_score >= 0.70:
            tier = TranslationFidelityTier.COMMUNITY_VERIFIED
        else:
            tier = TranslationFidelityTier.MACHINE_RAW_PREVIEW

        return MultilingualTranslationResult(
            translation_id=translation_id.strip(),
            source_locale=source_locale.strip().lower(),
            target_locale=target_locale.strip().lower(),
            fidelity_tier=tier,
            semantic_similarity_score=round(semantic_similarity_score, 2),
            translated_text=translated_text.strip(),
        )
