from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FacilitationMode(StrEnum):
    SOCRATIC_INQUIRY_PROMPT = "SOCRATIC_INQUIRY_PROMPT"
    NONVIOLENT_REFRAMING_SYNTHESIS = "NONVIOLENT_REFRAMING_SYNTHESIS"
    COMMON_GROUND_SURFACING = "COMMON_GROUND_SURFACING"


@dataclass(frozen=True, slots=True)
class FacilitationResult:
    intervention_id: str
    deliberation_room_id: str
    mode: FacilitationMode
    neutrality_index: float
    deescalation_efficacy_score: float
    facilitation_prompt_text: str


class AiNeutralityFacilitatorService:
    @staticmethod
    def generate_intervention(
        *,
        intervention_id: str,
        deliberation_room_id: str,
        mode: FacilitationMode,
        neutrality_index: float,
        deescalation_efficacy_score: float,
        facilitation_prompt_text: str,
    ) -> FacilitationResult:
        if not 0.0 <= neutrality_index <= 1.0:
            raise ValueError(f"neutrality_index must be in [0.0, 1.0], got {neutrality_index}")
        if not 0.0 <= deescalation_efficacy_score <= 1.0:
            raise ValueError(f"deescalation_efficacy_score must be in [0.0, 1.0], got {deescalation_efficacy_score}")
        if len(facilitation_prompt_text.strip()) < 10:
            raise ValueError("facilitation_prompt_text must have at least 10 characters")

        return FacilitationResult(
            intervention_id=intervention_id.strip(),
            deliberation_room_id=deliberation_room_id.strip(),
            mode=mode,
            neutrality_index=round(neutrality_index, 2),
            deescalation_efficacy_score=round(deescalation_efficacy_score, 2),
            facilitation_prompt_text=facilitation_prompt_text.strip(),
        )
