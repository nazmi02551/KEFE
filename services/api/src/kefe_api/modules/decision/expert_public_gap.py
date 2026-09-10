from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class GapClassification(StrEnum):
    CONVERGENT = "CONVERGENT"
    TECHNICAL_TRANSLATION_GAP = "TECHNICAL_TRANSLATION_GAP"
    NORMATIVE_VALUE_DIVERGENCE = "NORMATIVE_VALUE_DIVERGENCE"
    TRUST_DEFICIT_SKEPTICISM = "TRUST_DEFICIT_SKEPTICISM"


MIN_EXPERT_SAMPLE_SIZE: int = 30
MIN_PUBLIC_SAMPLE_SIZE: int = 100


@dataclass(frozen=True, slots=True)
class ExpertPublicGapResult:
    case_version_id: str
    expert_sample_size: int
    public_sample_size: int
    expert_distribution: dict[str, float]
    public_distribution: dict[str, float]
    gap_magnitude_points: int
    gap_classification: GapClassification
    key_divergence_drivers: list[str]
    epistemic_bridges: list[str]
    generated_at: str

    def to_dict(self) -> dict:
        return {
            "case_version_id": self.case_version_id,
            "expert_sample_size": self.expert_sample_size,
            "public_sample_size": self.public_sample_size,
            "expert_distribution": self.expert_distribution,
            "public_distribution": self.public_distribution,
            "gap_magnitude_points": self.gap_magnitude_points,
            "gap_classification": self.gap_classification.value,
            "key_divergence_drivers": list(self.key_divergence_drivers),
            "epistemic_bridges": list(self.epistemic_bridges),
            "generated_at": self.generated_at,
        }


class ExpertPublicGapService:
    @staticmethod
    def classify_gap(
        gap_points: int,
        *,
        trust_deficit: bool = False,
    ) -> GapClassification:
        if trust_deficit:
            return GapClassification.TRUST_DEFICIT_SKEPTICISM
        if gap_points <= 10:
            return GapClassification.CONVERGENT
        if gap_points <= 25:
            return GapClassification.TECHNICAL_TRANSLATION_GAP
        return GapClassification.NORMATIVE_VALUE_DIVERGENCE

    @classmethod
    def get_gap_analysis(cls, case_version_id: str) -> ExpertPublicGapResult:
        expert_dist = {"A": 0.78, "B": 0.22}
        public_dist = {"A": 0.46, "B": 0.54}

        gap_points = round(abs(expert_dist["A"] - public_dist["A"]) * 100)
        classification = cls.classify_gap(gap_points)

        drivers = [
            "Teknik risk ve uzun vadeli modelleme algısındaki metodolojik asimetri.",
            "Günlük yaşam ve maliyet etkilerine karşı teorik fayda optimizasyonu ayrışması.",
            "Kurumsal şeffaflık ve denetim mekanizmalarına duyulan güven farkı.",
        ]

        bridges = [
            "Karmaşık teknik raporların sadeleştirilmiş açık metodoloji özetleriyle sunulması.",
            "Önceliklendirilen risk eşiklerinin yurttaş panellerinde doğrudan test edilmesi.",
            "Kademeli geçiş döneminde bağımsız sivil izleme mekanizmalarının işletilmesi.",
        ]

        return ExpertPublicGapResult(
            case_version_id=case_version_id,
            expert_sample_size=85,
            public_sample_size=940,
            expert_distribution=expert_dist,
            public_distribution=public_dist,
            gap_magnitude_points=gap_points,
            gap_classification=classification,
            key_divergence_drivers=drivers,
            epistemic_bridges=bridges,
            generated_at=datetime.now(UTC).isoformat(),
        )
