from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class DutyNatureEnum(StrEnum):
    LEGAL_LIABILITY = "LEGAL_LIABILITY"
    REGULATORY_OVERSIGHT = "REGULATORY_OVERSIGHT"
    OPERATIONAL_EXECUTION = "OPERATIONAL_EXECUTION"
    FIDUCIARY_ETHICAL_DUTY = "FIDUCIARY_ETHICAL_DUTY"


@dataclass(frozen=True, slots=True)
class ActorResponsibilityItem:
    actor_key: str
    actor_name: str
    responsibility_share: float
    duty_nature: DutyNatureEnum
    jurisdiction_scope: str
    accountability_mechanism: str = ""

    def to_dict(self) -> dict:
        return {
            "actor_key": self.actor_key,
            "actor_name": self.actor_name,
            "responsibility_share": round(self.responsibility_share, 4),
            "duty_nature": self.duty_nature.value,
            "jurisdiction_scope": self.jurisdiction_scope,
            "accountability_mechanism": self.accountability_mechanism,
        }


@dataclass(frozen=True, slots=True)
class ResponsibilityAnalysisResult:
    analysis_id: str
    case_version_id: UUID
    clarity_score: float
    has_accountability_gap: bool
    legal_redress_channel: str
    actor_allocations: list[ActorResponsibilityItem]
    gap_explanation: str | None = None

    def to_dict(self) -> dict:
        return {
            "analysis_id": self.analysis_id,
            "case_version_id": str(self.case_version_id),
            "clarity_score": round(self.clarity_score, 4),
            "has_accountability_gap": self.has_accountability_gap,
            "legal_redress_channel": self.legal_redress_channel,
            "gap_explanation": self.gap_explanation,
            "actor_allocations": [a.to_dict() for a in self.actor_allocations],
        }


class ResponsibilityAnalysisCalculator:
    @staticmethod
    def analyze(
        *,
        analysis_id: str,
        case_version_id: UUID,
        clarity_score: float,
        has_accountability_gap: bool,
        legal_redress_channel: str,
        actor_allocations: list[ActorResponsibilityItem],
        gap_explanation: str | None = None,
    ) -> ResponsibilityAnalysisResult:
        if not 0.0 <= clarity_score <= 1.0:
            raise ValueError(f"clarity_score must be in [0.0, 1.0], got {clarity_score}")
        if len(legal_redress_channel.strip()) < 3:
            raise ValueError("legal_redress_channel must have at least 3 characters")
        if not actor_allocations:
            raise ValueError("actor_allocations cannot be empty")

        for item in actor_allocations:
            if not 0.0 <= item.responsibility_share <= 1.0:
                raise ValueError(
                    f"responsibility_share must be in [0.0, 1.0], got {item.responsibility_share}"
                )

        return ResponsibilityAnalysisResult(
            analysis_id=analysis_id.strip(),
            case_version_id=case_version_id,
            clarity_score=clarity_score,
            has_accountability_gap=has_accountability_gap,
            legal_redress_channel=legal_redress_channel.strip(),
            actor_allocations=actor_allocations,
            gap_explanation=gap_explanation.strip() if gap_explanation else None,
        )

    @classmethod
    def compute_for_case(cls, case_version_id: UUID) -> ResponsibilityAnalysisResult:
        """Deterministic institutional responsibility allocation for a case."""
        actors = [
            ActorResponsibilityItem(
                actor_key="REGULATORY_AUTHORITY",
                actor_name="Düzenleyici ve Denetleyici Üst Kurul",
                responsibility_share=0.40,
                duty_nature=DutyNatureEnum.REGULATORY_OVERSIGHT,
                jurisdiction_scope="Sektörel standart belirleme, lisanslama ve periyodik denetim",
                accountability_mechanism="İdari para cezaları, lisans iptali ve meclis denetimi",
            ),
            ActorResponsibilityItem(
                actor_key="OPERATIONAL_EXECUTOR",
                actor_name="İşletmeci / Uygulayıcı Kuruluş",
                responsibility_share=0.35,
                duty_nature=DutyNatureEnum.OPERATIONAL_EXECUTION,
                jurisdiction_scope="Hizmet sunumu, teknik altyapı güvenliği ve risk yönetimi",
                accountability_mechanism="Hukuki tazminat ve sözleşmesel taahhütler",
            ),
            ActorResponsibilityItem(
                actor_key="CENTRAL_MINISTRY",
                actor_name="İlgili Bakanlık / Kamu Otoritesi",
                responsibility_share=0.15,
                duty_nature=DutyNatureEnum.LEGAL_LIABILITY,
                jurisdiction_scope="Mevzuat hazırlığı, kamu yararı gözetimi ve nihai idari vesayet",
                accountability_mechanism="Danıştay / İdare Mahkemeleri yargısal denetimi",
            ),
            ActorResponsibilityItem(
                actor_key="CIVIC_CONSUMERS",
                actor_name="Kullanıcılar ve Sivil Toplum",
                responsibility_share=0.10,
                duty_nature=DutyNatureEnum.FIDUCIARY_ETHICAL_DUTY,
                jurisdiction_scope="Bilinçli kullanım, bildirim ve şikayet mekanizmalarını işletme",
                accountability_mechanism="Tüketici Hakem Heyetleri ve ombudsman başvuruları",
            ),
        ]

        return cls.analyze(
            analysis_id=f"RESP-{case_version_id.hex[:8]}",
            case_version_id=case_version_id,
            clarity_score=0.82,
            has_accountability_gap=False,
            legal_redress_channel="İdare Mahkemesi & Kamu Denetçiliği Kurumu (Ombudsmanlık)",
            actor_allocations=actors,
            gap_explanation=None,
        )
