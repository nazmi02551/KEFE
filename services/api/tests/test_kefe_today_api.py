from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_get_today_case_projection() -> None:
    app = create_app()
    client = TestClient(app)

    res = client.get("/v1/today/case")
    assert res.status_code == 200
    data = res.json()

    assert data["contract_id"] == "KEFE-TODAY-REAL-EVENT-PROJECTION-001"
    assert "CAP-026" in data["capabilities"]
    assert data["is_real_event"] is True
    assert len(data["title"]) >= 5
    assert len(data["editorial_headline"]) >= 5


def test_curate_new_today_case() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    payload = {
        "case_id": "case-water-rationing-2026",
        "case_version_id": str(case_version_id),
        "title": "Kentsel Kuraklık ve Su Kotası Uygulaması",
        "summary": "Baraj doluluk oranlarının düşmesi karşısında sanayi ve konut su kotalarının kademelendirilmesi.",
        "editorial_headline": "Günün Sıcak Olayı: Su Krizinde Öncelik Dağılımı",
        "is_real_event": True,
        "domain": "Environment",
    }

    curate_res = client.post("/v1/today/curate", json=payload)
    assert curate_res.status_code == 200
    curated = curate_res.json()
    assert curated["case_id"] == payload["case_id"]
    assert curated["title"] == payload["title"]
    assert curated["is_real_event"] is True

    # Check that subsequent GET returns updated curation
    get_res = client.get("/v1/today/case")
    assert get_res.status_code == 200
    assert get_res.json()["case_id"] == payload["case_id"]
