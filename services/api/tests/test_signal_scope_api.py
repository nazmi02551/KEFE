from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_signal_scope_api() -> None:
    app = create_app()
    client = TestClient(app)

    signal_id = "77777777-7777-4777-8777-777777777701"
    res = client.get(f"/v1/signals/{signal_id}/scope-alignment")
    assert res.status_code == 200
    data = res.json()

    assert data["signal_id"] == signal_id
    assert data["jurisdiction_level"] == "MUNICIPAL"
    assert data["alignment_status"] == "STRICTLY_ALIGNED"
    assert data["overall_alignment_score"] >= 0.85
    assert len(data["scope_seal_hash"]) == 64
    assert data["validity_window_days"] == 90
    assert "Istanbul" in data["geographic_scope"] or "İstanbul" in data["geographic_scope"]

    dimensions = data["dimensions"]
    assert len(dimensions) == 4
    for dim in dimensions:
        assert "dimension" in dim
        assert "declared_scope" in dim
        assert "sample_scope" in dim
        assert 0.0 <= dim["alignment_score"] <= 1.0
        assert isinstance(dim["is_valid"], bool)
