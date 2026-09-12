from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_get_methodology_disclosure_trusted_high_confidence() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/v1/methodology/case/test-case-101?sample_size=250")
    assert response.status_code == 200

    data = response.json()
    assert data["contract_id"] == "KEFE-OPEN-METHODOLOGY-DISCLOSURE-001"
    assert data["capability_id"] == "CAP-074"
    assert data["engine_version"] == "v1.0"
    assert data["target_type"] == "case"
    assert data["target_id"] == "test-case-101"
    assert data["layer"] == "TRUSTED"
    assert data["confidence"] == "HIGH"
    assert data["sample_size"] == 250
    assert len(data["safeguards"]) >= 3
    assert len(data["methodology_hash"]) == 64
    assert data["invariants"]["no_psychometric_claims"] is True


def test_get_methodology_disclosure_degraded_insufficient() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/v1/methodology/signal/sig-999?sample_size=4")
    assert response.status_code == 200

    data = response.json()
    assert data["layer"] == "DEGRADED"
    assert data["confidence"] == "INSUFFICIENT"
    assert data["sample_size"] == 4


def test_get_methodology_disclosure_invalid_target_type() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/v1/methodology/invalid_type/123")
    assert response.status_code == 400
    assert "Invalid target_type" in response.json()["detail"]


def test_get_methodology_manifest_summary() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/v1/methodology/manifest/summary")
    assert response.status_code == 200

    data = response.json()
    assert data["engine_version"] == "v1.0"
    assert "formula_manifest" in data
    assert "consensus_score" in data["formula_manifest"]
    assert "depolarization_index" in data["formula_manifest"]
    assert "safeguard_definitions" in data
    assert "COMMIT_FIRST" in data["safeguard_definitions"]
