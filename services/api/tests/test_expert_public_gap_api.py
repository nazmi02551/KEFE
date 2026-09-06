from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_expert_public_gap_api_get() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_id}/expert-public-gap")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert data["expert_sample_size"] >= 30
    assert data["public_sample_size"] >= 100

    assert len(data["expert_distribution"]) > 0
    assert len(data["public_distribution"]) > 0

    valid_classes = [
        "CONVERGENT",
        "TECHNICAL_TRANSLATION_GAP",
        "NORMATIVE_VALUE_DIVERGENCE",
        "TRUST_DEFICIT_SKEPTICISM",
    ]
    assert data["gap_classification"] in valid_classes
    assert 0 <= data["gap_magnitude_points"] <= 100
    assert len(data["key_divergence_drivers"]) >= 2
    assert len(data["epistemic_bridges"]) >= 2
