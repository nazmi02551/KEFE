from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_context_lens_api_default_pillars() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    res = client.get(f"/v1/cases/{case_version_id}/context-lens")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_version_id
    assert len(data["pillars"]) >= 3
    pillar_types = [p["pillar_type"] for p in data["pillars"]]
    assert "LEGAL_FRAMEWORK" in pillar_types
    assert "COMPARATIVE_PRACTICE" in pillar_types
    assert "SCIENTIFIC_DATA" in pillar_types


def test_context_lens_api_add_pillar() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    payload = {
        "pillar_type": "COMPARATIVE_PRACTICE",
        "title": "Tokyo ve Singapur Akıllı Şehir Bütçe Sübvansiyonu",
        "content": "Asya metropollerindeki akıllı ulaşım hatları kamu-özel ortaklığı ve algoritmik talep optimizasyonu ile sübvanse edilmektedir.",
        "source_citation": "Tokyo Metropolitan Transport Authority Report 2025",
        "source_url": "https://metro.tokyo.jp/transport",
    }

    res = client.post(f"/v1/cases/{case_id}/context-lens/pillars", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "CREATED"
    assert res_data["pillar"]["pillar_type"] == "COMPARATIVE_PRACTICE"
    assert res_data["pillar"]["title"] == "Tokyo ve Singapur Akıllı Şehir Bütçe Sübvansiyonu"

    # Fetch and verify
    get_res = client.get(f"/v1/cases/{case_id}/context-lens")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert len(get_data["pillars"]) == 1
    assert get_data["pillars"][0]["source_citation"].startswith("Tokyo Metropolitan")


def test_context_lens_api_validation_errors() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())

    # Invalid pillar_type
    res_invalid_type = client.post(
        f"/v1/cases/{case_id}/context-lens/pillars",
        json={
            "pillar_type": "UNKNOWN_TYPE",
            "title": "Geçersiz Tip Başlığı",
            "content": "Bu içerik en az yirmi karakter uzunluğundadır.",
            "source_citation": "Kaynak 1",
        },
    )
    assert res_invalid_type.status_code == 422

    # Too short content (< 20 chars)
    res_short = client.post(
        f"/v1/cases/{case_id}/context-lens/pillars",
        json={
            "pillar_type": "LEGAL_FRAMEWORK",
            "title": "Kısa",
            "content": "Kısa",
            "source_citation": "Kaynak 2",
        },
    )
    assert res_short.status_code == 422
