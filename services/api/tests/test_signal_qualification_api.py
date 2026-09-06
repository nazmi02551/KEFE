from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_signal_qualification_api() -> None:
    app = create_app()
    client = TestClient(app)

    signal_id = "77777777-7777-4777-8777-777777777701"
    res = client.get(f"/v1/signals/{signal_id}/qualification")
    assert res.status_code == 200
    data = res.json()

    assert data["signal_id"] == signal_id
    assert data["qualification_status"] == "QUALIFIED"
    assert data["qualification_tier"] == "GOLD_STANDARD"
    assert data["overall_score"] >= 0.80
    assert data["sample_size"] == 1420
    assert len(data["qualification_audit_hash"]) == 64

    criteria = data["criteria"]
    assert len(criteria) == 5
    expected_crit_ids = {
        "sample_sufficiency",
        "contribution_integrity",
        "entropy_diversity",
        "deliberation_depth",
        "astroturfing_immunity",
    }
    actual_crit_ids = {c["criterion_id"] for c in criteria}
    assert actual_crit_ids == expected_crit_ids

    for c in criteria:
        assert c["is_passed"] is True
        assert len(c["name_tr"]) > 0
        assert len(c["name_en"]) > 0
        assert len(c["audit_note"]) > 0

    assert len(data["eligible_channels"]) == 4
    assert "CIVIC_PUBLIC_DASHBOARD" in data["eligible_channels"]
    assert "POLICY_DELIBERATION_REPORT" in data["eligible_channels"]
