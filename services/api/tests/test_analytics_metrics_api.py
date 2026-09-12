from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app

client = TestClient(create_app())


def test_get_north_star_metrics() -> None:
    response = client.get("/v1/analytics/north-star?window_days=7")
    assert response.status_code == 200
    data = response.json()
    assert "meaningful_weigh_count" in data
    assert "weekly_active_weighers" in data
    assert "distinct_cases_weighed" in data
    assert data["meaningful_weigh_count"] >= 0
    assert data["weekly_active_weighers"] >= 0
    assert data["distinct_cases_weighed"] >= 0
    assert "window_start" in data
    assert "window_end" in data


def test_get_activation_funnel() -> None:
    response = client.get("/v1/analytics/funnel?window_days=14")
    assert response.status_code == 200
    data = response.json()
    assert "total_sessions" in data
    assert data["total_sessions"] > 0
    assert "stages" in data
    stage_names = [s["stage_name"] for s in data["stages"]]
    assert "WEIGH_STARTED" in stage_names
    assert "DECISION_COMMITTED" in stage_names
    assert "RESULT_REVEALED" in stage_names
    assert "PERSPECTIVE_VIEWED" in stage_names
    assert "DECISION_REVISED" in stage_names

    # Check stage properties
    first_stage = data["stages"][0]
    assert "conversion_from_start_rate" in first_stage
    assert "drop_off_from_previous_rate" in first_stage


def test_get_quality_metrics() -> None:
    response = client.get("/v1/analytics/quality?window_days=7")
    assert response.status_code == 200
    data = response.json()
    assert "total_exposed_sessions" in data
    assert "stable_decisions_count" in data
    assert "shifted_decisions_count" in data
    assert "resilience_index" in data
    assert "attitude_shift_rate" in data
    assert 0.0 <= data["resilience_index"] <= 1.0
    assert 0.0 <= data["attitude_shift_rate"] <= 1.0


def test_depolarization_evaluate_high_depolarization() -> None:
    case_id = str(uuid4())
    response = client.post(
        "/v1/analytics/depolarization/evaluate",
        json={
            "case_version_id": case_id,
            "pre_deliberation_distance": 0.80,
            "post_deliberation_distance": 0.30,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_version_id"] == case_id
    assert data["bridge_efficacy_state"] == "HIGH_DEPOLARIZATION"
    assert data["depolarization_score"] > 0.5


def test_depolarization_evaluate_persistent_polarization() -> None:
    case_id = str(uuid4())
    response = client.post(
        "/v1/analytics/depolarization/evaluate",
        json={
            "case_version_id": case_id,
            "pre_deliberation_distance": 0.85,
            "post_deliberation_distance": 0.80,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["case_version_id"] == case_id
    assert data["bridge_efficacy_state"] == "PERSISTENT_POLARIZATION"
    assert data["depolarization_score"] < 0.20


def test_depolarization_evaluate_validation_error() -> None:
    case_id = str(uuid4())
    response = client.post(
        "/v1/analytics/depolarization/evaluate",
        json={
            "case_version_id": case_id,
            "pre_deliberation_distance": 1.5,  # invalid > 1.0
            "post_deliberation_distance": 0.4,
        },
    )
    assert response.status_code == 422
