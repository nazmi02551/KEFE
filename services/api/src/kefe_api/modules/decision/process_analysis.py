from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ProcessStageEnum(StrEnum):
    CONSULTATION = "CONSULTATION"
    DRAFTING = "DRAFTING"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    PUBLIC_HEARING = "PUBLIC_HEARING"
    DECISION_ENACTED = "DECISION_ENACTED"
    POST_IMPLEMENTATION_AUDIT = "POST_IMPLEMENTATION_AUDIT"


class TransparencyLevel(StrEnum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    RESTRICTED = "RESTRICTED"
    OPAQUE = "OPAQUE"


class PublicParticipationStatus(StrEnum):
    OPEN_CONSULTATION = "OPEN_CONSULTATION"
    INVITED_STAKEHOLDERS_ONLY = "INVITED_STAKEHOLDERS_ONLY"
    FORMAL_NOTICE_ONLY = "FORMAL_NOTICE_ONLY"
    EXECUTIVE_BYPASS = "EXECUTIVE_BYPASS"


@dataclass(frozen=True, slots=True)
class ProcessStageItem:
    stage_key: str
    stage_title: str
    is_completed: bool
    duration_days: int
    has_public_input: bool
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "stage_key": self.stage_key,
            "stage_title": self.stage_title,
            "is_completed": self.is_completed,
            "duration_days": self.duration_days,
            "has_public_input": self.has_public_input,
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class ProcessAnalysisResult:
    analysis_id: str
    case_version_id: UUID
    current_stage: ProcessStageEnum
    procedural_integrity_score: float
    transparency_level: TransparencyLevel
    public_participation_status: PublicParticipationStatus
    oversight_body: str
    stages: list[ProcessStageItem]
    procedural_bottleneck: str | None = None

    def to_dict(self) -> dict:
        return {
            "analysis_id": self.analysis_id,
            "case_version_id": str(self.case_version_id),
            "current_stage": self.current_stage.value,
            "procedural_integrity_score": round(self.procedural_integrity_score, 4),
            "transparency_level": self.transparency_level.value,
            "public_participation_status": self.public_participation_status.value,
            "oversight_body": self.oversight_body,
            "procedural_bottleneck": self.procedural_bottleneck,
            "stages": [s.to_dict() for s in self.stages],
        }


class ProcessAnalysisCalculator:
    @staticmethod
    def analyze(
        *,
        analysis_id: str,
        case_version_id: UUID,
        current_stage: ProcessStageEnum,
        procedural_integrity_score: float,
        transparency_level: TransparencyLevel,
        public_participation_status: PublicParticipationStatus,
        oversight_body: str,
        stages: list[ProcessStageItem],
        procedural_bottleneck: str | None = None,
    ) -> ProcessAnalysisResult:
        if not 0.0 <= procedural_integrity_score <= 1.0:
            raise ValueError(
                f"procedural_integrity_score must be in [0.0, 1.0], got {procedural_integrity_score}"
            )
        if len(oversight_body.strip()) < 3:
            raise ValueError("oversight_body must have at least 3 characters")
        if not stages:
            raise ValueError("stages cannot be empty")

        return ProcessAnalysisResult(
            analysis_id=analysis_id.strip(),
            case_version_id=case_version_id,
            current_stage=current_stage,
            procedural_integrity_score=procedural_integrity_score,
            transparency_level=transparency_level,
            public_participation_status=public_participation_status,
            oversight_body=oversight_body.strip(),
            stages=stages,
            procedural_bottleneck=procedural_bottleneck.strip() if procedural_bottleneck else None,
        )

    @classmethod
    def compute_for_case(cls, case_version_id: UUID) -> ProcessAnalysisResult:
        """Deterministic procedural analysis for a case."""
        stages = [
            ProcessStageItem(
                stage_key="CONSULTATION",
                stage_title="Kamu Danışması ve Paydaş Katılımı",
                is_completed=True,
                duration_days=30,
                has_public_input=True,
                notes="Çevrimiçi açık çağrı ve sivil toplum görüşleri toplandı.",
            ),
            ProcessStageItem(
                stage_key="LEGAL_REVIEW",
                stage_title="Hukuki Uyum ve Norm Denetimi",
                is_completed=True,
                duration_days=14,
                has_public_input=False,
                notes="Anayasal haklar ve mevzuat uyumluluğu incelendi.",
            ),
            ProcessStageItem(
                stage_key="PUBLIC_HEARING",
                stage_title="Açık Oturum ve Komisyon Değerlendirmesi",
                is_completed=True,
                duration_days=7,
                has_public_input=True,
                notes="Tutanaklar şeffaf olarak kamuya açıldı.",
            ),
            ProcessStageItem(
                stage_key="DECISION_ENACTED",
                stage_title="Karar İlanı ve Gerekçeli Rapor",
                is_completed=True,
                duration_days=5,
                has_public_input=False,
                notes="Gerekçeli karar ve karşı oylar yayımlandı.",
            ),
            ProcessStageItem(
                stage_key="POST_IMPLEMENTATION_AUDIT",
                stage_title="Uygulama Sonrası Bağımsız Etki Denetimi",
                is_completed=False,
                duration_days=90,
                has_public_input=True,
                notes="6 aylık bağımsız izleme süreci devam ediyor.",
            ),
        ]

        completed_count = sum(1 for s in stages if s.is_completed)
        public_count = sum(1 for s in stages if s.has_public_input)
        integrity = min(1.0, max(0.0, (completed_count / len(stages)) * 0.6 + (public_count / len(stages)) * 0.4))

        return cls.analyze(
            analysis_id=f"PROC-{case_version_id.hex[:8]}",
            case_version_id=case_version_id,
            current_stage=ProcessStageEnum.DECISION_ENACTED,
            procedural_integrity_score=integrity,
            transparency_level=TransparencyLevel.HIGH if integrity >= 0.7 else TransparencyLevel.MODERATE,
            public_participation_status=PublicParticipationStatus.OPEN_CONSULTATION,
            oversight_body="Bağımsız Denetim ve Ombudsmanlık",
            stages=stages,
            procedural_bottleneck=None,
        )
