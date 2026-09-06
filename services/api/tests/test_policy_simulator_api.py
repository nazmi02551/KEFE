from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.policy_simulator import EquilibriumState


def test_policy_simulator_api_default() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_id}/policy-simulations")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert data["knob_value"] == 50.0
    assert data["equilibrium_state"] in [e.value for e in EquilibriumState]
    assert 0.0 <= data["fiscal_score"] <= 1.0
    assert 0.0 <= data["social_score"] <= 1.0
    assert 0.0 <= data["environmental_score"] <= 1.0


def test_policy_simulator_api_evaluate() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.post(
        f"/v1/cases/{case_id}/policy-simulations/evaluate",
        json={"knob_value": 85.0, "policy_knob_name": "Yeşil Dönüşüm Fonu"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert data["knob_value"] == 85.0
    assert data["policy_knob_name"] == "Yeşil Dönüşüm Fonu"
    assert data["equilibrium_state"] in [e.value for e in EquilibriumState]
