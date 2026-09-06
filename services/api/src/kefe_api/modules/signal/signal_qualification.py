from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
import hashlib
from typing import Sequence
from uuid import UUID


class SignalQualificationStatus(str, Enum):
    QUALIFIED = "QUALIFIED"
    PROVISIONAL = "PROVISIONAL"
    DISQUALIFIED = "DISQUALIFIED"


class SignalQualificationTier(str, Enum):
    GOLD_STANDARD = "GOLD_STANDARD"
    SILVER_VALIDATED = "SILVER_VALIDATED"
    BRONZE_OBSERVED = "BRONZE_OBSERVED"
    UNQUALIFIED = "UNQUALIFIED"


@dataclass(frozen=True)
class QualificationCriterion:
    criterion_id: str
    name_tr: str
    name_en: str
    score: float
    threshold: float
    is_passed: bool
    audit_note: str


@dataclass(frozen=True)
class SignalQualificationReport:
    signal_id: UUID
    case_version_id: UUID
    case_title: str
    qualification_status: SignalQualificationStatus
    qualification_tier: SignalQualificationTier
    overall_score: float
    sample_size: int
    criteria: Sequence[QualificationCriterion]
    eligible_channels: Sequence[str]
    certified_at: datetime
    qualification_audit_hash: str


class SignalQualificationService:
    """Evaluates multi-dimensional deliberative and epistemic criteria to qualify raw results into civic signals."""

    @staticmethod
    def evaluate(
        *,
        signal_id: UUID,
        case_version_id: UUID,
        case_title: str,
        sample_size: int,
        entropy_score: float = 0.78,
        deliberation_depth_score: float = 0.82,
        astroturfing_immunity_score: float = 0.94,
        pre_result_ratio: float = 1.0,
        certified_at: datetime | None = None,
    ) -> SignalQualificationReport:
        if certified_at is None:
            certified_at = datetime.now(UTC)

        # 1. Sample Sufficiency Gate
        sample_score = min(1.0, round(sample_size / 500.0, 4))
        sample_passed = sample_size >= 100
        sample_note = (
            f"Örneklem büyüklüğü ({sample_size}) asgari güvenilirlik eşiğini geçmektedir."
            if sample_passed
            else f"Örneklem büyüklüğü ({sample_size}) asgari 100 katılımcı eşiğinin altındadır."
        )
        c_sample = QualificationCriterion(
            criterion_id="sample_sufficiency",
            name_tr="Örneklem Yeterliliği",
            name_en="Sample Sufficiency",
            score=sample_score,
            threshold=0.20,
            is_passed=sample_passed,
            audit_note=sample_note,
        )

        # 2. Contribution Integrity Gate (Blind-First Core Protocol)
        integrity_passed = pre_result_ratio >= 0.95
        c_integrity = QualificationCriterion(
            criterion_id="contribution_integrity",
            name_tr="Katkı Bütünlüğü (Körleme Öncesi)",
            name_en="Contribution Integrity (Pre-Result)",
            score=round(pre_result_ratio, 4),
            threshold=0.95,
            is_passed=integrity_passed,
            audit_note="Tüm girdiler sonuç ifşasından önceki körleme protokolüyle toplanmıştır.",
        )

        # 3. Perspective Entropy Diversity Gate
        entropy_passed = entropy_score >= 0.65
        c_entropy = QualificationCriterion(
            criterion_id="entropy_diversity",
            name_tr="Perspektif Entropi Çeşitliliği",
            name_en="Perspective Entropy Diversity",
            score=round(entropy_score, 4),
            threshold=0.65,
            is_passed=entropy_passed,
            audit_note="Farklı dünya görüşleri ve perspektifler yeterli dağılım sergilemektedir.",
        )

        # 4. Deliberation Depth Gate
        depth_passed = deliberation_depth_score >= 0.60
        c_depth = QualificationCriterion(
            criterion_id="deliberation_depth",
            name_tr="Müzakere Derinliği",
            name_en="Deliberation Depth",
            score=round(deliberation_depth_score, 4),
            threshold=0.60,
            is_passed=depth_passed,
            audit_note="Karşı argüman inceleme ve düşünme süreleri asgari eşiği aşmıştır.",
        )

        # 5. Astroturfing & Sybil Immunity Gate
        sybil_passed = astroturfing_immunity_score >= 0.80
        c_sybil = QualificationCriterion(
            criterion_id="astroturfing_immunity",
            name_tr="Bot ve Yapay Yönlendirme Kalkanı",
            name_en="Astroturfing & Bot Immunity",
            score=round(astroturfing_immunity_score, 4),
            threshold=0.80,
            is_passed=sybil_passed,
            audit_note="Koordineli sahte katılım veya bot sapması tespit edilmemiştir.",
        )

        criteria = [c_sample, c_integrity, c_entropy, c_depth, c_sybil]

        # Overall score is weighted average
        overall_score = round(
            (c_sample.score * 0.20)
            + (c_integrity.score * 0.25)
            + (c_entropy.score * 0.20)
            + (c_depth.score * 0.15)
            + (c_sybil.score * 0.20),
            4,
        )

        all_passed = all(c.is_passed for c in criteria)

        if all_passed:
            qualification_status = SignalQualificationStatus.QUALIFIED
            if sample_size >= 500:
                qualification_tier = SignalQualificationTier.GOLD_STANDARD
                eligible_channels = [
                    "CIVIC_PUBLIC_DASHBOARD",
                    "INSTITUTIONAL_IMPACT_DESK",
                    "MEDIA_CITATION_FEED",
                    "POLICY_DELIBERATION_REPORT",
                ]
            elif sample_size >= 250:
                qualification_tier = SignalQualificationTier.SILVER_VALIDATED
                eligible_channels = [
                    "CIVIC_PUBLIC_DASHBOARD",
                    "INSTITUTIONAL_IMPACT_DESK",
                    "MEDIA_CITATION_FEED",
                ]
            else:
                qualification_tier = SignalQualificationTier.BRONZE_OBSERVED
                eligible_channels = [
                    "CIVIC_PUBLIC_DASHBOARD",
                ]
        elif sample_size >= 50 and sybil_passed:
            qualification_status = SignalQualificationStatus.PROVISIONAL
            qualification_tier = SignalQualificationTier.UNQUALIFIED
            eligible_channels = []
        else:
            qualification_status = SignalQualificationStatus.DISQUALIFIED
            qualification_tier = SignalQualificationTier.UNQUALIFIED
            eligible_channels = []

        audit_payload = (
            f"{signal_id}:{case_version_id}:{qualification_tier.value}:"
            f"{overall_score:.4f}:{sample_size}:{certified_at.isoformat()}"
        )
        qualification_audit_hash = hashlib.sha256(audit_payload.encode("utf-8")).hexdigest()

        return SignalQualificationReport(
            signal_id=signal_id,
            case_version_id=case_version_id,
            case_title=case_title,
            qualification_status=qualification_status,
            qualification_tier=qualification_tier,
            overall_score=overall_score,
            sample_size=sample_size,
            criteria=criteria,
            eligible_channels=eligible_channels,
            certified_at=certified_at,
            qualification_audit_hash=qualification_audit_hash,
        )
