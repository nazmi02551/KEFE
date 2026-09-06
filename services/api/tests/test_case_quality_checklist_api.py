from __future__ import annotations

from uuid import UUID
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.case_quality_checklist import (
    CaseQualityChecklistEvaluator,
    QualityAuditStatus,
)


def test_case_quality_checklist_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    res = client.get(f"/v1/cases/{case_version_id}/quality-checklist")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_version_id
    assert data["overall_status"] == "FULLY_AUDITED_PASS"
    assert data["verified_count"] == 8
    assert data["total_count"] == 8
    assert data["methodology_hash"] == "sha256-kefe-cqb-chk-8dim-7a19c"

    items = data["items"]
    assert len(items) == 8

    expected_dimensions = {
        "BALANCED_OPTIONS",
        "NEUTRAL_PROVENANCE",
        "DISCLOSED_STAKEHOLDERS",
        "VERIFIED_SOURCES",
        "ACCESSIBLE_READABILITY",
        "PRINCIPLE_INTEGRITY",
        "REASON_PROMPT_EQUITY",
        "METHODOLOGY_TRANSPARENCY",
    }
    actual_dimensions = {item["dimension_id"] for item in items}
    assert actual_dimensions == expected_dimensions

    for item in items:
        assert item["status"] == "VERIFIED"
        assert len(item["name_tr"]) > 0
        assert len(item["name_en"]) > 0
        assert len(item["criterion_tr"]) > 0
        assert len(item["criterion_en"]) > 0
        assert len(item["reviewer_note"]) > 0


def test_case_quality_checklist_evaluator_flagged_status() -> None:
    evaluator = CaseQualityChecklistEvaluator()
    case_id = "test-case-flagged"
    result = evaluator.evaluate(
        case_id,
        custom_statuses={
            "BALANCED_OPTIONS": (
                QualityAuditStatus.FLAGGED,
                "Seçenek A bariz biçimde karikatürize edilmiş.",
            )
        },
    )

    assert result.case_version_id == case_id
    assert result.overall_status == "NEEDS_EDITORIAL_REVISION"
    assert result.verified_count == 7
    assert result.total_count == 8

    d = result.to_dict()
    assert d["overall_status"] == "NEEDS_EDITORIAL_REVISION"
    assert d["verified_count"] == 7
