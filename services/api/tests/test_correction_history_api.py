from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_get_case_correction_history_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    res = client.get(f"/v1/cases/{case_version_id}/corrections")
    assert res.status_code == 200
    data = res.json()
    assert data["case_version_id"] == case_version_id
    corrections = data["corrections"]
    assert isinstance(corrections, list)
    assert len(corrections) >= 1

    first = corrections[0]
    assert "correction_id" in first
    assert first["correction_type"] == "FACTUAL_UPDATE"
    assert first["severity"] == "MINOR"
    assert "madde numarası güncellendi" in first["summary"]
    assert "2026 revizyonu" in first["editorial_rationale"]
    assert first["previous_text"] == "Madde 14 uyarınca"
    assert first["corrected_text"] == "Madde 16/A uyarınca"
