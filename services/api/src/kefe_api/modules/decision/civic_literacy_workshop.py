from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LiteracyModuleType(StrEnum):
    FALLACY_SPOTTING = "FALLACY_SPOTTING"
    ETHICAL_FRAMEWORKS = "ETHICAL_FRAMEWORKS"
    EVIDENCE_EVALUATION = "EVIDENCE_EVALUATION"
    BRIDGE_SYNTHESIS = "BRIDGE_SYNTHESIS"


@dataclass(frozen=True, slots=True)
class CivicLiteracyWorkshopResult:
    workshop_id: str
    module_type: LiteracyModuleType
    module_title: str
    total_drills: int
    completed_drills: int
    comprehension_score: float


class CivicLiteracyWorkshopService:
    @staticmethod
    def evaluate_progress(
        *,
        workshop_id: str,
        module_type: LiteracyModuleType,
        module_title: str,
        total_drills: int,
        completed_drills: int,
        correct_answers: int,
    ) -> CivicLiteracyWorkshopResult:
        if total_drills < 1:
            raise ValueError("total_drills must be at least 1")
        if not 0 <= completed_drills <= total_drills:
            raise ValueError(f"completed_drills must be in [0, {total_drills}]")
        if not 0 <= correct_answers <= completed_drills:
            raise ValueError(f"correct_answers must be in [0, {completed_drills}]")
        if len(module_title.strip()) < 5:
            raise ValueError("module_title must have at least 5 characters")

        score = correct_answers / completed_drills if completed_drills > 0 else 0.0

        return CivicLiteracyWorkshopResult(
            workshop_id=workshop_id.strip(),
            module_type=module_type,
            module_title=module_title.strip(),
            total_drills=total_drills,
            completed_drills=completed_drills,
            comprehension_score=round(score, 2),
        )
