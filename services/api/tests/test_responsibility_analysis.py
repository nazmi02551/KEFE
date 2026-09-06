from __future__ import annotations

from uuid import uuid4
import pytest

from kefe_api.modules.decision.responsibility_analysis import (
    ActorResponsibilityItem,
    DutyNatureEnum,
    ResponsibilityAnalysisCalculator,
    ResponsibilityAnalysisResult,
)


def test_responsibility_analysis_calculator_valid() -> None:
    case_id = uuid4()
    actors = [
        ActorResponsibilityItem(
            actor_key="REGULATOR",
            actor_name="Denetim Kurulu",
            responsibility_share=0.6,
            duty_nature=DutyNatureEnum.REGULATORY_OVERSIGHT,
            jurisdiction_scope="Sektörel denetim",
            accountability_mechanism="İdari para cezası",
        ),
        ActorResponsibilityItem(
            actor_key="OPERATOR",
            actor_name="İşletmeci Şirket",
            responsibility_share=0.4,
            duty_nature=DutyNatureEnum.OPERATIONAL_EXECUTION,
            jurisdiction_scope="Altyapı bakımı",
            accountability_mechanism="Tazminat",
        ),
    ]

    result = ResponsibilityAnalysisCalculator.analyze(
        analysis_id="resp-test-01",
        case_version_id=case_id,
        clarity_score=0.90,
        has_accountability_gap=False,
        legal_redress_channel="Danıştay / İdare Mahkemeleri",
        actor_allocations=actors,
        gap_explanation=None,
    )

    assert result.analysis_id == "resp-test-01"
    assert result.case_version_id == case_id
    assert result.clarity_score == 0.90
    assert not result.has_accountability_gap
    assert len(result.actor_allocations) == 2

    d = result.to_dict()
    assert d["analysis_id"] == "resp-test-01"
    assert d["clarity_score"] == 0.90
    assert len(d["actor_allocations"]) == 2


def test_responsibility_analysis_validation_errors() -> None:
    case_id = uuid4()
    with pytest.raises(ValueError, match="clarity_score must be in"):
        ResponsibilityAnalysisCalculator.analyze(
            analysis_id="r1",
            case_version_id=case_id,
            clarity_score=1.5,
            has_accountability_gap=False,
            legal_redress_channel="Mahkeme",
            actor_allocations=[
                ActorResponsibilityItem("A", "Kurum", 0.5, DutyNatureEnum.LEGAL_LIABILITY, "Kapsam")
            ],
        )

    with pytest.raises(ValueError, match="legal_redress_channel must have at least 3 characters"):
        ResponsibilityAnalysisCalculator.analyze(
            analysis_id="r1",
            case_version_id=case_id,
            clarity_score=0.8,
            has_accountability_gap=False,
            legal_redress_channel="M",
            actor_allocations=[
                ActorResponsibilityItem("A", "Kurum", 0.5, DutyNatureEnum.LEGAL_LIABILITY, "Kapsam")
            ],
        )


def test_responsibility_analysis_compute_for_case() -> None:
    case_id = uuid4()
    result = ResponsibilityAnalysisCalculator.compute_for_case(case_id)
    assert result.case_version_id == case_id
    assert 0.0 <= result.clarity_score <= 1.0
    assert len(result.actor_allocations) >= 3
    total_share = sum(a.responsibility_share for a in result.actor_allocations)
    assert 0.99 <= total_share <= 1.01
