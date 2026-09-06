from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_signal_versioning_api() -> None:
    app = create_app()
    client = TestClient(app)

    signal_id = "77777777-7777-4777-8777-777777777701"
    res = client.get(f"/v1/signals/{signal_id}/versioning")
    assert res.status_code == 200
    data = res.json()

    assert data["signal_id"] == signal_id
    assert data["current_version"] == "v1.2.0-entropy"
    assert len(data["current_methodology_hash"]) == 64
    assert data["audit_chain_valid"] is True

    snapshots = data["snapshots"]
    assert len(snapshots) == 2
    assert snapshots[0]["methodology_version"] == "v1.0.0"
    assert snapshots[0]["parent_snapshot_hash"] is None
    assert snapshots[1]["methodology_version"] == "v1.2.0-entropy"
    assert snapshots[1]["parent_snapshot_hash"] == snapshots[0]["snapshot_hash"]

    delta = data["latest_delta"]
    assert delta is not None
    assert delta["from_version"] == "v1.0.0"
    assert delta["to_version"] == "v1.2.0-entropy"
    assert delta["distribution_shift"] == 0.02
