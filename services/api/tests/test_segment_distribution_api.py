from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_segment_distribution_api_get() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_id}/segment-distributions")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert data["minimum_sample_threshold"] == 30
    assert data["overall_sample_size"] > 0
    assert len(data["segments"]) > 0

    # Verify privacy guarantees
    guarantees = data["privacy_guarantees"]
    assert guarantees["k_anonymity_threshold"] == 30
    assert guarantees["no_individual_profiling"] is True
    assert guarantees["differential_privacy_noise_applied"] is True

    # Validate individual segment data
    for seg in data["segments"]:
        assert seg["cohort_type"] in [
            "AGE_COHORT",
            "URBAN_RURAL_COHORT",
            "EXPERIENCE_LEVEL",
            "REGIONAL_COHORT",
            "STAKEHOLDER_ROLE",
        ]
        assert len(seg["cohort_label"]) > 0
        if seg["is_suppressed"]:
            assert seg["sample_size"] < 30
            assert seg["suppression_reason"] == "INSUFFICIENT_SAMPLE_PRIVACY_THRESHOLD"
            assert seg["option_shares"] == {}
            assert seg["primary_choice"] is None
        else:
            assert seg["sample_size"] >= 30
            assert seg["suppression_reason"] is None
            assert len(seg["option_shares"]) > 0
            assert seg["primary_choice"] is not None
            assert 0.0 <= seg["entropy_score"] <= 1.0
