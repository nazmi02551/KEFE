from __future__ import annotations

from uuid import uuid4
import pytest

from kefe_api.modules.decision.process_analysis import (
    ProcessAnalysisCalculator,
    ProcessAnalysisResult,
    ProcessStageEnum,
    ProcessStageItem,
    PublicParticipationStatus,
    TransparencyLevel,
)


def test_process_analysis_calculator_valid() -> None:
    case_id = uuid4()
    stages = [
        ProcessStageItem(
            stage_key="CONSULTATION",
            stage_title="Kamu İstişaresi",
            is_completed=True,
            duration_days=20,
            has_public_input=True,
            notes="Görüşler derlendi.",
        ),
        ProcessStageItem(
            stage_key="LEGAL_REVIEW",
            stage_title="Hukuk İncelemesi",
            is_completed=True,
            duration_days=10,
            has_public_input=False,
            notes="Norm denetimi tamamlandı.",
        ),
    ]

    result = ProcessAnalysisCalculator.analyze(
        analysis_id="proc-101",
        case_version_id=case_id,
        current_stage=ProcessStageEnum.LEGAL_REVIEW,
        procedural_integrity_score=0.88,
        transparency_level=TransparencyLevel.HIGH,
        public_participation_status=PublicParticipationStatus.OPEN_CONSULTATION,
        oversight_body="Danıştay / Sayıştay",
        stages=stages,
        procedural_bottleneck=None,
    )

    assert result.analysis_id == "proc-101"
    assert result.case_version_id == case_id
    assert result.current_stage == ProcessStageEnum.LEGAL_REVIEW
    assert result.procedural_integrity_score == 0.88
    assert result.transparency_level == TransparencyLevel.HIGH
    assert result.public_participation_status == PublicParticipationStatus.OPEN_CONSULTATION
    assert len(result.stages) == 2

    d = result.to_dict()
    assert d["analysis_id"] == "proc-101"
    assert d["current_stage"] == "LEGAL_REVIEW"
    assert d["procedural_integrity_score"] == 0.88


def test_process_analysis_calculator_validation_errors() -> None:
    case_id = uuid4()
    with pytest.raises(ValueError, match="procedural_integrity_score must be in"):
        ProcessAnalysisCalculator.analyze(
            analysis_id="p1",
            case_version_id=case_id,
            current_stage=ProcessStageEnum.DRAFTING,
            procedural_integrity_score=1.5,
            transparency_level=TransparencyLevel.MODERATE,
            public_participation_status=PublicParticipationStatus.FORMAL_NOTICE_ONLY,
            oversight_body="Kurul",
            stages=[ProcessStageItem("DRAFT", "Taslak", True, 5, False)],
        )

    with pytest.raises(ValueError, match="oversight_body must have at least 3 characters"):
        ProcessAnalysisCalculator.analyze(
            analysis_id="p1",
            case_version_id=case_id,
            current_stage=ProcessStageEnum.DRAFTING,
            procedural_integrity_score=0.5,
            transparency_level=TransparencyLevel.MODERATE,
            public_participation_status=PublicParticipationStatus.FORMAL_NOTICE_ONLY,
            oversight_body="K",
            stages=[ProcessStageItem("DRAFT", "Taslak", True, 5, False)],
        )


def test_process_analysis_compute_for_case() -> None:
    case_id = uuid4()
    result = ProcessAnalysisCalculator.compute_for_case(case_id)
    assert result.case_version_id == case_id
    assert 0.0 <= result.procedural_integrity_score <= 1.0
    assert len(result.stages) >= 3
    assert result.transparency_level in [TransparencyLevel.HIGH, TransparencyLevel.MODERATE]
