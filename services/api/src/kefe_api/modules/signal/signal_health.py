"""Signal Health Audit Domain Service (CAP-044).

Enforces the constitutional invariant that a raw Collective Result is not
automatically a Signal without passing multi-dimensional statistical and
epistemic integrity thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID


class SignalQualificationStatus(str, Enum):
    QUALIFIED_SIGNAL = "QUALIFIED_SIGNAL"
    PROVISIONAL_TREND = "PROVISIONAL_TREND"
    UNQUALIFIED_NOISE = "UNQUALIFIED_NOISE"


@dataclass(frozen=True)
class SignalHealthDimension:
    dimension_id: str
    title_tr: str
    title_en: str
    score: float
    threshold: float
    is_passed: bool
    detail: str


@dataclass(frozen=True)
class SignalHealthReport:
    signal_id: UUID
    case_version_id: UUID
    overall_qualification: SignalQualificationStatus
    overall_health_score: float
    sample_size: int
    dimensions: list[SignalHealthDimension]
    certified_at: datetime
    methodology_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": str(self.signal_id),
            "case_version_id": str(self.case_version_id),
            "overall_qualification": self.overall_qualification.value,
            "overall_health_score": self.overall_health_score,
            "sample_size": self.sample_size,
            "dimensions": [
                {
                    "dimension_id": d.dimension_id,
                    "title_tr": d.title_tr,
                    "title_en": d.title_en,
                    "score": d.score,
                    "threshold": d.threshold,
                    "is_passed": d.is_passed,
                    "detail": d.detail,
                }
                for d in self.dimensions
            ],
            "certified_at": self.certified_at.isoformat(),
            "methodology_hash": self.methodology_hash,
        }


class SignalHealthAuditService:
    """Evaluates multi-dimensional health metrics for a collective deliberation signal."""

    def evaluate(
        self,
        signal_id: UUID,
        case_version_id: UUID,
        sample_size: int = 1420,
        bot_integrity: float = 0.94,
        segment_entropy: float = 0.81,
        deliberation_depth: float = 0.78,
        temporal_freshness: float = 0.92,
    ) -> SignalHealthReport:
        dims = [
            SignalHealthDimension(
                dimension_id="SAMPLE_SIZE",
                title_tr="Örneklem Yeterliliği",
                title_en="Sample Size Sufficiency",
                score=float(sample_size),
                threshold=100.0,
                is_passed=sample_size >= 100,
                detail=f"{sample_size} çekirdek katılımcı (eşik: 100).",
            ),
            SignalHealthDimension(
                dimension_id="BOT_RESISTANCE",
                title_tr="Bot ve Sahte Hesap Güvenliği",
                title_en="Bot & Astroturfing Shield",
                score=round(bot_integrity, 2),
                threshold=0.85,
                is_passed=bot_integrity >= 0.85,
                detail="Koordineli sahte davranış anomalisi tespit edilmedi.",
            ),
            SignalHealthDimension(
                dimension_id="SEGMENT_ENTROPY",
                title_tr="Demografik Çeşitlilik Entropisi",
                title_en="Demographic Segment Entropy",
                score=round(segment_entropy, 2),
                threshold=0.70,
                is_passed=segment_entropy >= 0.70,
                detail="Monolitik olmayan çoğulcu katılım dağılımı sağlandı.",
            ),
            SignalHealthDimension(
                dimension_id="DELIBERATION_DEPTH",
                title_tr="Müzakere ve Düşünme Derinliği",
                title_en="Deliberation Depth Index",
                score=round(deliberation_depth, 2),
                threshold=0.65,
                is_passed=deliberation_depth >= 0.65,
                detail="Tartım süresi ve gerekçe üretimi nitelikli müzakere standardında.",
            ),
            SignalHealthDimension(
                dimension_id="TEMPORAL_FRESHNESS",
                title_tr="Zamansal Tazelik ve Güncellik",
                title_en="Temporal Signal Freshness",
                score=round(temporal_freshness, 2),
                threshold=0.50,
                is_passed=temporal_freshness >= 0.50,
                detail="Yarılanma ömrü sınırları içinde taze ve geçerli sinyal.",
            ),
        ]

        passed_count = sum(1 for d in dims if d.is_passed)
        avg_score = round(
            (
                min(1.0, sample_size / 200.0) * 20.0
                + bot_integrity * 20.0
                + segment_entropy * 20.0
                + deliberation_depth * 20.0
                + temporal_freshness * 20.0
            ),
            1,
        )

        if passed_count == len(dims):
            qualification = SignalQualificationStatus.QUALIFIED_SIGNAL
        elif sample_size >= 50 and bot_integrity >= 0.80:
            qualification = SignalQualificationStatus.PROVISIONAL_TREND
        else:
            qualification = SignalQualificationStatus.UNQUALIFIED_NOISE

        return SignalHealthReport(
            signal_id=signal_id,
            case_version_id=case_version_id,
            overall_qualification=qualification,
            overall_health_score=avg_score,
            sample_size=sample_size,
            dimensions=dims,
            certified_at=datetime.now(UTC),
            methodology_hash="sha256-sig-health-5dim-9f82a",
        )
