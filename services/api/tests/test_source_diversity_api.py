from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_get_source_diversity_default_balanced() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    response = client.get(f"/v1/cases/{case_version_id}/source-diversity")
    assert response.status_code == 200

    data = response.json()
    assert data["case_version_id"] == str(case_version_id)
    assert data["total_sources"] == 4
    assert data["diversity_level"] in ("HIGH_DIVERSITY", "BALANCED_DIVERSITY")
    assert len(data["category_breakdown"]) >= 3


def test_evaluate_source_diversity_custom_categories() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    payload = {
        "source_categories": [
            "ACADEMIC_SCIENTIFIC",
            "OFFICIAL_GOVERNMENT",
            "CIVIC_INDEPENDENT",
            "MAINSTREAM_JOURNALISM",
            "TECHNICAL_INDUSTRY",
        ]
    }
    response = client.post(f"/v1/cases/{case_version_id}/source-diversity/evaluate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["total_sources"] == 5
    assert data["diversity_level"] == "HIGH_DIVERSITY"
    assert len(data["category_breakdown"]) == 5


def test_evaluate_source_diversity_limited_monopolistic() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    payload = {
        "source_categories": [
            "MAINSTREAM_JOURNALISM",
            "MAINSTREAM_JOURNALISM",
            "MAINSTREAM_JOURNALISM",
        ]
    }
    response = client.post(f"/v1/cases/{case_version_id}/source-diversity/evaluate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["total_sources"] == 3
    assert data["diversity_level"] == "LIMITED_DIVERSITY"
    assert len(data["category_breakdown"]) == 1
    assert data["category_breakdown"][0]["percentage"] == 100.0


def test_evaluate_source_diversity_invalid_category_fails() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    payload = {
        "source_categories": ["INVALID_BOGUS_CATEGORY"]
    }
    response = client.post(f"/v1/cases/{case_version_id}/source-diversity/evaluate", json=payload)
    assert response.status_code == 400
    assert "Invalid category" in response.json()["detail"]
