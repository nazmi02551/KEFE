from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RoleFlipResult:
    case_version_id: UUID
    initial_role: str
    flipped_role: str
    flipped_scenario_prompt: str
    perspective_shift_score: float


class RoleFlipCalculator:
    @staticmethod
    def evaluate(
        *,
        case_version_id: UUID,
        initial_role: str,
        flipped_role: str,
        flipped_scenario_prompt: str,
        perspective_shift_score: float,
    ) -> RoleFlipResult:
        if not 0.0 <= perspective_shift_score <= 1.0:
            raise ValueError(f"perspective_shift_score must be in [0.0, 1.0], got {perspective_shift_score}")
        if len(initial_role.strip()) < 3 or len(flipped_role.strip()) < 3:
            raise ValueError("Role names must have at least 3 characters")
        if len(flipped_scenario_prompt.strip()) < 10:
            raise ValueError("flipped_scenario_prompt must have at least 10 characters")

        return RoleFlipResult(
            case_version_id=case_version_id,
            initial_role=initial_role.strip(),
            flipped_role=flipped_role.strip(),
            flipped_scenario_prompt=flipped_scenario_prompt.strip(),
            perspective_shift_score=round(perspective_shift_score, 2),
        )
