from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class DepthLevel(StrEnum):
    PROFOUND_DELIBERATION = "PROFOUND_DELIBERATION"
    STRUCTURED_REFLECTION = "STRUCTURED_REFLECTION"
    SUPERFICIAL_SKIMMING = "SUPERFICIAL_SKIMMING"


@dataclass(frozen=True, slots=True)
class DeliberationDepthResult:
    case_version_id: UUID
    deliberation_depth_score: float
    depth_level: DepthLevel
    arguments_inspected_count: int
    evidence_items_verified_count: int
    counter_views_explored_count: int


class DeliberationDepthCalculator:
    @staticmethod
    def calculate(
        *,
        case_version_id: UUID,
        arguments_inspected_count: int,
        evidence_items_verified_count: int,
        counter_views_explored_count: int,
    ) -> DeliberationDepthResult:
        if arguments_inspected_count < 0:
            raise ValueError("arguments_inspected_count cannot be negative")
        if evidence_items_verified_count < 0:
            raise ValueError("evidence_items_verified_count cannot be negative")
        if counter_views_explored_count < 0:
            raise ValueError("counter_views_explored_count cannot be negative")

        arg_score = min(1.0, arguments_inspected_count / 8.0)
        evi_score = min(1.0, evidence_items_verified_count / 4.0)
        counter_score = min(1.0, counter_views_explored_count / 3.0)

        depth_score = (0.40 * arg_score) + (0.35 * evi_score) + (0.25 * counter_score)
        depth_score = max(0.0, min(1.0, depth_score))

        if depth_score >= 0.75:
            level = DepthLevel.PROFOUND_DELIBERATION
        elif depth_score >= 0.40:
            level = DepthLevel.STRUCTURED_REFLECTION
        else:
            level = DepthLevel.SUPERFICIAL_SKIMMING

        return DeliberationDepthResult(
            case_version_id=case_version_id,
            deliberation_depth_score=round(depth_score, 2),
            depth_level=level,
            arguments_inspected_count=arguments_inspected_count,
            evidence_items_verified_count=evidence_items_verified_count,
            counter_views_explored_count=counter_views_explored_count,
        )
