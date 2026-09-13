from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app

client = TestClient(create_app())


def test_get_case_lifecycle() -> None:
    res = client.get("/v1/cases/case_ai_001/lifecycle")
    assert res.status_code == 200
    data = res.json()
    assert data["case_id"] == "case_ai_001"
    assert data["current_case_version_id"] == "v2_ai_governance"
    assert data["version_number"] == 2
    assert data["is_published"] is True
    assert data["has_institutional_response"] is True


def test_reconcile_saved_cases_detects_version_shift() -> None:
    res = client.post(
        "/v1/cases/reconcile-saved",
        json={
            "saved_cases": [
                {
                    "case_id": "case_ai_001",
                    "saved_version_id": "v1_ai_legacy",  # Old version
                },
                {
                    "case_id": "case_edu_002",
                    "saved_version_id": "v1_curriculum_standard",  # Matching version, no update
                },
            ]
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_checked"] == 2
    assert data["updated_count"] == 1

    first = data["results"][0]
    assert first["case_id"] == "case_ai_001"
    assert first["has_update"] is True
    assert first["change_type"] == "VERSION_SHIFT"
    assert "güncellendi" in first["notification_label_tr"]

    second = data["results"][1]
    assert second["case_id"] == "case_edu_002"
    assert second["has_update"] is False
    assert second["change_type"] == "NONE"


def test_reconcile_saved_cases_validation_error() -> None:
    res = client.post(
        "/v1/cases/reconcile-saved",
        json={"saved_cases": []},  # min_length is 1
    )
    assert res.status_code == 422
