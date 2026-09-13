from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.temporal_drift import DriftNature
from kefe_api.modules.decision.fatigue_guard import PacingStatus


def test_temporal_drift_and_fatigue_guard_api() -> None:
    app = create_app()
    client = TestClient(app)
    case_id = str(uuid4())

    # 1. CAP-013: Temporal Drift API
    res_drift = client.get(f"/v1/cases/{case_id}/temporal-drift")
    assert res_drift.status_code == 200, res_drift.text
    data_drift = res_drift.json()
    assert data_drift["case_version_id"] == case_id
    assert data_drift["is_shifted"] is True
    assert data_drift["time_elapsed_days"] == 45
    assert data_drift["drift_nature"] == DriftNature.MATURED_REVISION.value
    assert data_drift["capability_id"] == "CAP-013"

    # 2. CAP-014: Fatigue Guard Status (GET)
    res_status = client.get("/v1/cases/fatigue-guard/status?session_id=SESS-100&consecutive_weigh_count=3&session_duration_minutes=12.0")
    assert res_status.status_code == 200, res_status.text
    data_status = res_status.json()
    assert data_status["session_id"] == "SESS-100"
    assert data_status["pacing_status"] == PacingStatus.OPTIMAL_PACING.value
    assert data_status["capability_id"] == "CAP-014"

    # 3. CAP-014: Fatigue Guard Evaluate (POST - Pacing Recommended)
    res_eval = client.post("/v1/cases/fatigue-guard/evaluate", json={
        "session_id": "SESS-200",
        "consecutive_weigh_count": 7,
        "session_duration_minutes": 25.0,
    })
    assert res_eval.status_code == 200, res_eval.text
    data_eval = res_eval.json()
    assert data_eval["session_id"] == "SESS-200"
    assert data_eval["pacing_status"] == PacingStatus.PACING_RECOMMENDED.value
    assert "önceki kararlarınızı gözden geçirebilirsiniz" in data_eval["gentle_recommendation_prompt"]

    # 4. CAP-014: Fatigue Guard Evaluate (POST - Rest Interval Active)
    res_rest = client.post("/v1/cases/fatigue-guard/evaluate", json={
        "session_id": "SESS-300",
        "consecutive_weigh_count": 12,
        "session_duration_minutes": 50.0,
    })
    assert res_rest.status_code == 200, res_rest.text
    data_rest = res_rest.json()
    assert data_rest["pacing_status"] == PacingStatus.REST_INTERVAL_ACTIVE.value
    assert "kısa bir mola vermeniz önerilir" in data_rest["gentle_recommendation_prompt"]
