from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class YouthSpaceFocusArea(StrEnum):
    CAMPUS_AND_EDUCATION_POLICY = "CAMPUS_AND_EDUCATION_POLICY"
    CLIMATE_AND_INTERGENERATIONAL = "CLIMATE_AND_INTERGENERATIONAL"
    DIGITAL_RIGHTS_AND_AI = "DIGITAL_RIGHTS_AND_AI"
    CIVIC_ENTREPRENEURSHIP = "CIVIC_ENTREPRENEURSHIP"


@dataclass(frozen=True, slots=True)
class YouthDeliberationSpaceResult:
    space_id: str
    space_name: str
    focus_area: YouthSpaceFocusArea
    institution_or_community: str
    active_student_count: int
    consensus_action_count: int


class YouthDeliberationSpaceService:
    @staticmethod
    def register_or_update_space(
        *,
        space_id: str,
        space_name: str,
        focus_area: YouthSpaceFocusArea,
        institution_or_community: str,
        active_student_count: int,
        consensus_action_count: int,
    ) -> YouthDeliberationSpaceResult:
        if len(space_name.strip()) < 5:
            raise ValueError("space_name must have at least 5 characters")
        if len(institution_or_community.strip()) < 3:
            raise ValueError("institution_or_community must have at least 3 characters")
        if active_student_count < 0:
            raise ValueError("active_student_count cannot be negative")
        if consensus_action_count < 0:
            raise ValueError("consensus_action_count cannot be negative")

        return YouthDeliberationSpaceResult(
            space_id=space_id.strip(),
            space_name=space_name.strip(),
            focus_area=focus_area,
            institution_or_community=institution_or_community.strip(),
            active_student_count=active_student_count,
            consensus_action_count=consensus_action_count,
        )
