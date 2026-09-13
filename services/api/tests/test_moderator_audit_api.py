from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_log_and_query_moderation_action() -> None:
    app = create_app()
    client = TestClient(app)

    payload = {
        "target_resource_id": "reason-target-999",
        "moderator_id": "moderator-beta-01",
        "action_type": "REASON_REMOVED_POLICY_BREACH",
        "policy_rule_reference": "KEFE-SEC-001/Section-3.1-Harassment",
        "justification_text": "Content contains targeted ad-hominem attack against participant cohort.",
    }

    create_res = client.post("/v1/moderation/audit", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()

    assert created["contract_id"] == "KEFE-MOD-AUDIT-001"
    assert created["capability_id"] == "CAP-067"
    assert created["action_type"] == payload["action_type"]
    assert len(created["action_hash"]) == 64
    assert created["moderator_id"] == payload["moderator_id"]

    audit_id = created["audit_id"]

    # Retrieve single entry
    get_res = client.get(f"/v1/moderation/audit/{audit_id}")
    assert get_res.status_code == 200
    assert get_res.json()["audit_id"] == audit_id

    # List entries with filter
    list_res = client.get("/v1/moderation/audit?action_type=REASON_REMOVED_POLICY_BREACH")
    assert list_res.status_code == 200
    entries = list_res.json()
    assert any(e["audit_id"] == audit_id for e in entries)


def test_log_moderation_invalid_action_fails() -> None:
    app = create_app()
    client = TestClient(app)

    payload = {
        "target_resource_id": "res-123",
        "moderator_id": "mod-1",
        "action_type": "INVALID_UNKNOWN_ACTION",
        "policy_rule_reference": "KEFE-SEC-001",
        "justification_text": "Some text explaining reason removal.",
    }

    res = client.post("/v1/moderation/audit", json=payload)
    assert res.status_code == 400
    assert "Invalid action_type" in res.json()["detail"]
