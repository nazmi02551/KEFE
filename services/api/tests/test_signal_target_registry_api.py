from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_signal_target_registry_api() -> None:
    app = create_app()
    client = TestClient(app)

    signal_id = "77777777-7777-4777-8777-777777777701"
    res = client.get(f"/v1/signals/{signal_id}/targets")
    assert res.status_code == 200
    data = res.json()

    assert data["signal_id"] == signal_id
    assert len(data["registry_proof_hash"]) == 64
    assert len(data["targets"]) == 2

    primary = data["targets"][0]
    assert primary["target_id"] == data["primary_target_id"]
    assert primary["target_type"] == "MUNICIPAL_GOVERNMENT"
    assert primary["dispatch_status"] == "ACKNOWLEDGED"
    assert primary["response_due_days"] == 30
    assert "@" in primary["official_contact_channel"]
