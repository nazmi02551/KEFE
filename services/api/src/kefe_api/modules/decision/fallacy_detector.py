from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class FallacyType(StrEnum):
    AD_HOMINEM = "AD_HOMINEM"
    STRAW_MAN = "STRAW_MAN"
    FALSE_DILEMMA = "FALSE_DILEMMA"
    SLIPPERY_SLOPE = "SLIPPERY_SLOPE"
    APPEAL_TO_EMOTION_FEAR = "APPEAL_TO_EMOTION_FEAR"
    NO_FALLACY_DETECTED = "NO_FALLACY_DETECTED"


@dataclass(frozen=True, slots=True)
class DetectedFallacyItem:
    fallacy_type: FallacyType
    confidence: float
    explanation: str


@dataclass(frozen=True, slots=True)
class FallacyDetectionResult:
    argument_id: UUID
    has_fallacy: bool
    overall_integrity_score: float
    detected_fallacies: tuple[DetectedFallacyItem, ...]


class CognitiveFallacyDetector:
    @staticmethod
    def evaluate(
        argument_id: UUID,
        findings: list[DetectedFallacyItem],
    ) -> FallacyDetectionResult:
        if not findings:
            clean_item = DetectedFallacyItem(
                fallacy_type=FallacyType.NO_FALLACY_DETECTED,
                confidence=1.0,
                explanation="Argümanda belirgin bir mantıksal safsata veya bilişsel çarpıtma tespit edilmedi.",
            )
            return FallacyDetectionResult(
                argument_id=argument_id,
                has_fallacy=False,
                overall_integrity_score=1.0,
                detected_fallacies=(clean_item,),
            )

        actual_fallacies = [
            f for f in findings if f.fallacy_type != FallacyType.NO_FALLACY_DETECTED
        ]

        if not actual_fallacies:
            return FallacyDetectionResult(
                argument_id=argument_id,
                has_fallacy=False,
                overall_integrity_score=1.0,
                detected_fallacies=tuple(findings),
            )

        # Integrity deduction per fallacy severity/confidence
        max_penalty = min(0.9, sum(f.confidence * 0.35 for f in actual_fallacies))
        integrity = round(max(0.1, 1.0 - max_penalty), 2)

        return FallacyDetectionResult(
            argument_id=argument_id,
            has_fallacy=True,
            overall_integrity_score=integrity,
            detected_fallacies=tuple(actual_fallacies),
        )
