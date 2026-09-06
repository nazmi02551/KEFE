from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.fallacy_detector import (
    CognitiveFallacyDetector,
    DetectedFallacyItem,
    FallacyDetectionResult,
    FallacyType,
)


def test_cognitive_fallacy_detector_identifies_fallacies_and_penalties() -> None:
    arg_id = uuid4()

    # 1. Clean argument (No Fallacies)
    r1 = CognitiveFallacyDetector.evaluate(arg_id, [])
    assert isinstance(r1, FallacyDetectionResult)
    assert r1.has_fallacy is False
    assert r1.overall_integrity_score == 1.0

    # 2. Argument with Straw Man and Slippery Slope
    findings = [
        DetectedFallacyItem(
            fallacy_type=FallacyType.STRAW_MAN,
            confidence=0.8,
            explanation="Karşı tarafın argümanı aşırı basitleştirilerek çarpıtılmış.",
        ),
        DetectedFallacyItem(
            fallacy_type=FallacyType.SLIPPERY_SLOPE,
            confidence=0.7,
            explanation="Kanıt olmaksızın felaket senaryoları zinciri varsayılmış.",
        ),
    ]
    r2 = CognitiveFallacyDetector.evaluate(arg_id, findings)
    assert r2.has_fallacy is True
    assert len(r2.detected_fallacies) == 2
    assert r2.overall_integrity_score < 1.0
