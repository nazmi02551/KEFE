from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app

client = TestClient(create_app())


def test_publish_and_get_drift_notices() -> None:
    case_version_id = str(uuid4())
    res = client.post(
        f"/v1/cases/{case_version_id}/drift-notices",
        json={
            "drift_type": "LEGAL_REFORM",
            "summary": "İlgili yönetmelik maddesi Danıştay kararıyla iptal edilmiştir.",
            "recommended_action": "REVIEW_AMENDMENT",
            "source_reference_url": "https://danistay.gov.tr/karar-2026",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["case_version_id"] == case_version_id
    assert data["drift_type"] == "LEGAL_REFORM"
    assert data["recommended_action"] == "REVIEW_AMENDMENT"
    assert "notice_id" in data

    # Get notices
    get_res = client.get(f"/v1/cases/{case_version_id}/drift-notices")
    assert get_res.status_code == 200
    notices = get_res.json()
    assert len(notices) == 1
    assert notices[0]["summary"].startswith("İlgili yönetmelik")


def test_get_live_radar_pulse() -> None:
    case_version_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_version_id}/live-radar")
    assert res.status_code == 200
    data = res.json()
    assert data["case_version_id"] == case_version_id
    assert "deliberation_velocity_index" in data
    assert "live_participant_count" in data
    assert "shift_vectors" in data
    assert len(data["shift_vectors"]) >= 3
    assert data["live_participant_count"] > 0
