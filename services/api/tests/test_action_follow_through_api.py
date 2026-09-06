from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_list_and_propose_actions_endpoint() -> None:
    app = create_app()
    client = TestClient(app)

    # 1. List pre-seeded actions
    res = client.get("/v1/impact/actions")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    first = data[0]
    assert "action_id" in first
    assert "title" in first
    assert first["status"] in [
        "PROPOSED",
        "IN_PROGRESS",
        "VERIFIED_COMPLETE",
        "STALLED",
    ]
    assert 0 <= first["progress_percentage"] <= 100

    # 2. Propose new action
    case_version_id = "22222222-2222-4222-8222-222222222222"
    propose_res = client.post(
        "/v1/impact/actions",
        json={
            "case_version_id": case_version_id,
            "title": "Yeni Yurttaş İnisiyatifi ve İzleme Kurulu",
            "description": "Topluluk kararlarının yerel idareye iletilmesi ve aylık raporlama yapılması.",
        },
    )
    assert propose_res.status_code == 201
    action_data = propose_res.json()
    action_id = action_data["action_id"]
    assert action_data["status"] == "PROPOSED"
    assert action_data["progress_percentage"] == 0

    # 3. Update progress with evidence
    patch_res = client.patch(
        f"/v1/impact/actions/{action_id}/progress",
        json={
            "case_version_id": case_version_id,
            "progress_percentage": 50,
            "status": "IN_PROGRESS",
            "evidence_summary": "İlk izleme toplantısı yapıldı ve tutanak tutuldu.",
            "evidence_url": "https://kefe.org/izleme/rapor-1",
        },
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["progress_percentage"] == 50
    assert updated_data["status"] == "IN_PROGRESS"
    assert updated_data["evidence_url"] == "https://kefe.org/izleme/rapor-1"
