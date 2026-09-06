from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class BlindMode(StrEnum):
    ACTOR_BLIND = "ACTOR_BLIND"
    SOURCE_BLIND = "SOURCE_BLIND"
    OUTCOME_BLIND = "OUTCOME_BLIND"


@dataclass(frozen=True, slots=True)
class BlindVariantsResult:
    case_version_id: UUID
    blind_mode: BlindMode
    blinded_prompt: str
    real_identity_revealed: str
    neutrality_score: float


class BlindVariantsCalculator:
    @staticmethod
    def evaluate(
        *,
        case_version_id: UUID,
        blind_mode: BlindMode,
        blinded_prompt: str,
        real_identity_revealed: str,
        neutrality_score: float,
    ) -> BlindVariantsResult:
        if not 0.0 <= neutrality_score <= 1.0:
            raise ValueError(f"neutrality_score must be in [0.0, 1.0], got {neutrality_score}")
        if len(blinded_prompt.strip()) < 10:
            raise ValueError("blinded_prompt must have at least 10 characters")
        if len(real_identity_revealed.strip()) < 5:
            raise ValueError("real_identity_revealed must have at least 5 characters")

        return BlindVariantsResult(
            case_version_id=case_version_id,
            blind_mode=blind_mode,
            blinded_prompt=blinded_prompt.strip(),
            real_identity_revealed=real_identity_revealed.strip(),
            neutrality_score=round(neutrality_score, 2),
        )
