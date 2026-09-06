from __future__ import annotations

from kefe_api.modules.decision.civic_literacy_workshop import (
    CivicLiteracyWorkshopResult,
    CivicLiteracyWorkshopService,
    LiteracyModuleType,
)


def test_civic_literacy_workshop_evaluates_progress() -> None:
    r = CivicLiteracyWorkshopService.evaluate_progress(
        workshop_id="wsp_001",
        module_type=LiteracyModuleType.FALLACY_SPOTTING,
        module_title="Safsata ve Çarpıtma Teşhisi",
        total_drills=10,
        completed_drills=8,
        correct_answers=7,  # 7/8 = 0.875 -> 0.88
    )

    assert isinstance(r, CivicLiteracyWorkshopResult)
    assert r.module_type == LiteracyModuleType.FALLACY_SPOTTING
    assert r.comprehension_score == 0.88
    assert r.completed_drills == 8


def test_civic_literacy_invalid_drills() -> None:
    failed = False
    try:
        CivicLiteracyWorkshopService.evaluate_progress(
            workshop_id="wsp_002",
            module_type=LiteracyModuleType.ETHICAL_FRAMEWORKS,
            module_title="Etik",  # < 5
            total_drills=5,
            completed_drills=6,  # > total
            correct_answers=4,
        )
    except ValueError:
        failed = True

    assert failed is True
