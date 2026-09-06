from __future__ import annotations

from kefe_api.modules.decision.youth_deliberation_space import (
    YouthDeliberationSpaceResult,
    YouthDeliberationSpaceService,
    YouthSpaceFocusArea,
)


def test_youth_deliberation_space_registers_properly() -> None:
    r = YouthDeliberationSpaceService.register_or_update_space(
        space_id="spc_001",
        space_name="ODTÜ Kampüs Ulaşım ve Yaya Güvenliği Müzakeresi",
        focus_area=YouthSpaceFocusArea.CAMPUS_AND_EDUCATION_POLICY,
        institution_or_community="Orta Doğu Teknik Üniversitesi",
        active_student_count=350,
        consensus_action_count=4,
    )

    assert isinstance(r, YouthDeliberationSpaceResult)
    assert r.focus_area == YouthSpaceFocusArea.CAMPUS_AND_EDUCATION_POLICY
    assert r.active_student_count == 350


def test_youth_space_invalid_name() -> None:
    failed = False
    try:
        YouthDeliberationSpaceService.register_or_update_space(
            space_id="spc_002",
            space_name="Kısa",  # < 5
            focus_area=YouthSpaceFocusArea.CLIMATE_AND_INTERGENERATIONAL,
            institution_or_community="Lise",
            active_student_count=10,
            consensus_action_count=0,
        )
    except ValueError:
        failed = True

    assert failed is True
