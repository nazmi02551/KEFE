from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PacingStatus(StrEnum):
    OPTIMAL_PACING = "OPTIMAL_PACING"
    PACING_RECOMMENDED = "PACING_RECOMMENDED"
    REST_INTERVAL_ACTIVE = "REST_INTERVAL_ACTIVE"


@dataclass(frozen=True, slots=True)
class DecisionFatigueResult:
    session_id: str
    consecutive_weigh_count: int
    session_duration_minutes: float
    pacing_status: PacingStatus
    gentle_recommendation_prompt: str

    def to_dict(self) -> dict[str, any]:
        return {
            "session_id": self.session_id,
            "consecutive_weigh_count": self.consecutive_weigh_count,
            "session_duration_minutes": self.session_duration_minutes,
            "pacing_status": self.pacing_status.value,
            "gentle_recommendation_prompt": self.gentle_recommendation_prompt,
            "capability_id": "CAP-014",
        }


class DecisionFatigueCalculator:
    @classmethod
    def evaluate_session(
        cls,
        session_id: str = "SESSION-DEFAULT",
        consecutive_weigh_count: int = 6,
        session_duration_minutes: float = 24.5,
    ) -> DecisionFatigueResult:
        """Deterministic session evaluation for pacing/fatigue (CAP-014)."""
        return cls.evaluate(
            session_id=session_id,
            consecutive_weigh_count=consecutive_weigh_count,
            session_duration_minutes=session_duration_minutes,
        )
    @staticmethod
    def evaluate(
        *,
        session_id: str,
        consecutive_weigh_count: int,
        session_duration_minutes: float,
    ) -> DecisionFatigueResult:
        if consecutive_weigh_count < 0:
            raise ValueError("consecutive_weigh_count cannot be negative")
        if session_duration_minutes < 0.0:
            raise ValueError("session_duration_minutes cannot be negative")
        if len(session_id.strip()) < 4:
            raise ValueError("session_id must have at least 4 characters")

        if consecutive_weigh_count >= 10 or session_duration_minutes >= 45.0:
            status = PacingStatus.REST_INTERVAL_ACTIVE
            prompt = "Bugün yoğun ve derinlikli tartımlar yaptınız. Zihninizi tazelemek ve sindirmek için kısa bir mola vermeniz önerilir."
        elif consecutive_weigh_count >= 5 or session_duration_minutes >= 20.0:
            status = PacingStatus.PACING_RECOMMENDED
            prompt = "Arka arkaya birkaç karmaşık ikilemi değerlendirdiniz. Dilerseniz önceki kararlarınızı gözden geçirebilirsiniz."
        else:
            status = PacingStatus.OPTIMAL_PACING
            prompt = "Zihinsel ritminiz dengeli ve odaklanmış durumda."

        return DecisionFatigueResult(
            session_id=session_id.strip(),
            consecutive_weigh_count=consecutive_weigh_count,
            session_duration_minutes=round(session_duration_minutes, 1),
            pacing_status=status,
            gentle_recommendation_prompt=prompt,
        )
