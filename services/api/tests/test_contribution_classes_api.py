from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_contribution_classes_api() -> None:
    app = create_app()
    client = TestClient(app)

    signal_id = "77777777-7777-4777-8777-777777777701"
    res = client.get(f"/v1/signals/{signal_id}/contribution-classes")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == "22222222-2222-4222-8222-222222222222"
    assert data["total_contributions"] == 1420 + 380 + 150
    assert data["contamination_risk_index"] == 0.0
    assert data["isolation_audit_status"] == "ENFORCED"
    assert len(data["isolation_proof_hash"]) == 64

    classes = data["classes"]
    assert len(classes) == 3
    expected_ids = {"CORE_PRE_RESULT", "EXPOSED", "ADVOCACY_SUPPORT"}
    actual_ids = {c["class_id"] for c in classes}
    assert actual_ids == expected_ids

    core = next(c for c in classes if c["class_id"] == "CORE_PRE_RESULT")
    assert core["is_signal_eligible"] is True
    assert core["count"] == 1420

    exposed = next(c for c in classes if c["class_id"] == "EXPOSED")
    assert exposed["is_signal_eligible"] is False
    assert exposed["count"] == 380

    advocacy = next(c for c in classes if c["class_id"] == "ADVOCACY_SUPPORT")
    assert advocacy["is_signal_eligible"] is False
    assert advocacy["count"] == 150
