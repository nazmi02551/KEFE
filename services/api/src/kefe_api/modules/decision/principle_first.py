from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class PrincipleType(StrEnum):
    INDIVIDUAL_LIBERTY = "INDIVIDUAL_LIBERTY"
    COLLECTIVE_WELLBEING = "COLLECTIVE_WELLBEING"
    PROCEDURAL_JUSTICE = "PROCEDURAL_JUSTICE"
    EMPATHY_COMPASSION = "EMPATHY_COMPASSION"


@dataclass(frozen=True, slots=True)
class PrincipleFirstResult:
    case_version_id: UUID
    primary_principle: PrincipleType
    secondary_principle: PrincipleType
    consistency_score: float
    reflection_prompt: str


class PrincipleFirstCalculator:
    @staticmethod
    def evaluate(
        *,
        case_version_id: UUID,
        primary_principle: PrincipleType,
        secondary_principle: PrincipleType,
        consistency_score: float,
        reflection_prompt: str,
    ) -> PrincipleFirstResult:
        if not 0.0 <= consistency_score <= 1.0:
            raise ValueError(f"consistency_score must be in [0.0, 1.0], got {consistency_score}")
        if len(reflection_prompt.strip()) < 5:
            raise ValueError("reflection_prompt must have at least 5 characters")

        return PrincipleFirstResult(
            case_version_id=case_version_id,
            primary_principle=primary_principle,
            secondary_principle=secondary_principle,
            consistency_score=round(consistency_score, 2),
            reflection_prompt=reflection_prompt.strip(),
        )
