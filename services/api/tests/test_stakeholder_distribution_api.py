from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_stakeholder_distribution_api_get() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_id}/stakeholder-distributions")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert data["total_stakeholders_represented"] > 0
    assert data["active_categories_count"] == 5
    assert len(data["stakeholder_distributions"]) == 5
    assert 0.0 <= data["pluralism_score"] <= 1.0

    valid_cats = [
        "DIRECTLY_IMPACTED",
        "FRONTLINE_PRACTITIONERS",
        "COMMERCIAL_ENTERPRISES",
        "REGULATORY_OVERSIGHT",
        "CIVIC_COMMUNITY",
    ]

    for item in data["stakeholder_distributions"]:
        assert item["category"] in valid_cats
        assert len(item["name"]) > 0
        assert item["participant_count"] > 0
        assert 0.0 <= item["sample_share"] <= 1.0
        assert len(item["option_shares"]) > 0
        assert item["primary_choice"] in item["option_shares"]
        assert 0.0 <= item["cohesion_index"] <= 1.0
        assert isinstance(item["divergence_from_overall_points"], int)
