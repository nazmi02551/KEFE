from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.normative_models import NormativePhilosophy


def test_normative_models_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_id}/normative-models")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert len(data["evaluations"]) >= 2
    assert "philosophies_explained_tr" in data
    assert "philosophies_explained_en" in data

    valid_philosophies = [e.value for e in NormativePhilosophy]
    for evaluation in data["evaluations"]:
        assert evaluation["dominant_philosophy"] in valid_philosophies
        assert 0.0 <= evaluation["utilitarian_score"] <= 1.0
        assert 0.0 <= evaluation["deontological_score"] <= 1.0
        assert 0.0 <= evaluation["rawlsian_score"] <= 1.0
        assert 0.0 <= evaluation["virtue_score"] <= 1.0

    for philosophy in valid_philosophies:
        assert philosophy in data["philosophies_explained_tr"]
        assert philosophy in data["philosophies_explained_en"]
