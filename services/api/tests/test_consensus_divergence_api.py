from __future__ import annotations

import json
from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.divergence_classifier import DivergenceClassification


def test_consensus_divergence_api_default() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_id}/consensus-divergence")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert data["classification"] in [e.value for e in DivergenceClassification]
    assert 0.0 <= data["leading_share"] <= 1.0
    assert 0.0 <= data["margin_of_divergence"] <= 1.0
    assert "label_tr" in data and len(data["label_tr"]) > 3
    assert "label_en" in data and len(data["label_en"]) > 3
    assert "description_tr" in data and len(data["description_tr"]) > 10
    assert "description_en" in data and len(data["description_en"]) > 10


def test_consensus_divergence_api_with_custom_distributions() -> None:
    app = create_app()
    client = TestClient(app)
    case_id = str(uuid4())

    # 1. Broad Consensus
    dist_broad = json.dumps({"opt_a": 0.82, "opt_b": 0.18})
    res = client.get(f"/v1/cases/{case_id}/consensus-divergence?distribution_json={dist_broad}")
    assert res.status_code == 200
    data = res.json()
    assert data["classification"] == "BROAD_CONSENSUS"
    assert data["leading_share"] == 0.82

    # 2. Bipolar Divergence
    dist_bipolar = json.dumps({"opt_a": 0.48, "opt_b": 0.44, "opt_c": 0.08})
    res = client.get(f"/v1/cases/{case_id}/consensus-divergence?distribution_json={dist_bipolar}")
    assert res.status_code == 200
    data = res.json()
    assert data["classification"] == "BIPOLAR_DIVERGENCE"
    assert data["margin_of_divergence"] == 0.04

    # 3. Fragmented Plurality
    dist_frag = json.dumps({"opt_a": 0.35, "opt_b": 0.33, "opt_c": 0.32})
    res = client.get(f"/v1/cases/{case_id}/consensus-divergence?distribution_json={dist_frag}")
    assert res.status_code == 200
    data = res.json()
    assert data["classification"] == "FRAGMENTED_PLURALITY"

    # 4. Leaning Majority
    dist_leaning = json.dumps({"opt_a": 0.65, "opt_b": 0.35})
    res = client.get(f"/v1/cases/{case_id}/consensus-divergence?distribution_json={dist_leaning}")
    assert res.status_code == 200
    data = res.json()
    assert data["classification"] == "LEANING_MAJORITY"


def test_consensus_divergence_api_invalid_json() -> None:
    app = create_app()
    client = TestClient(app)
    case_id = str(uuid4())

    res = client.get(f"/v1/cases/{case_id}/consensus-divergence?distribution_json=not-a-json")
    assert res.status_code == 400
