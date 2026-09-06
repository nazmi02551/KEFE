from __future__ import annotations

from kefe_api.modules.decision.ai_neutrality_facilitator import (
    AiNeutralityFacilitatorService,
    FacilitationMode,
    FacilitationResult,
)


def test_ai_neutrality_facilitates_socratic_prompt() -> None:
    r = AiNeutralityFacilitatorService.generate_intervention(
        intervention_id="fac_001",
        deliberation_room_id="room_001",
        mode=FacilitationMode.SOCRATIC_INQUIRY_PROMPT,
        neutrality_index=0.98,
        deescalation_efficacy_score=0.88,
        facilitation_prompt_text="Her iki taraf da kamu yararını amaçlıyor; peki kısa vadeli maliyetler nasıl dengelenebilir?",
    )

    assert isinstance(r, FacilitationResult)
    assert r.mode == FacilitationMode.SOCRATIC_INQUIRY_PROMPT
    assert r.neutrality_index == 0.98
    assert r.deescalation_efficacy_score == 0.88


def test_ai_neutrality_invalid_scores() -> None:
    failed = False
    try:
        AiNeutralityFacilitatorService.generate_intervention(
            intervention_id="fac_002",
            deliberation_room_id="room_002",
            mode=FacilitationMode.COMMON_GROUND_SURFACING,
            neutrality_index=1.20,  # > 1.0
            deescalation_efficacy_score=-0.5,  # < 0.0
            facilitation_prompt_text="Kısa",  # < 10
        )
    except ValueError:
        failed = True

    assert failed is True
