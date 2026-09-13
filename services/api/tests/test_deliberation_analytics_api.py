from __future__ import annotations

import json
from uuid import UUID
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_consensus_divergence_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    # Default distribution
    res = client.get(f"/v1/cases/{case_version_id}/consensus-divergence")
    assert res.status_code == 200
    data = res.json()
    assert data["case_version_id"] == case_version_id
    assert "classification" in data
    assert "leading_share" in data
    assert "margin_of_divergence" in data
    assert data["label_tr"] == "Kolektif Uzlaşı / Ayrışma Dağılımı"

    # Custom distribution query param
    custom_dist = json.dumps({"opt_a": 0.85, "opt_b": 0.15})
    res_custom = client.get(
        f"/v1/cases/{case_version_id}/consensus-divergence",
        params={"distribution_json": custom_dist},
    )
    assert res_custom.status_code == 200
    data_custom = res_custom.json()
    assert data_custom["classification"] == "BROAD_CONSENSUS"
    assert data_custom["leading_share"] == 0.85

    # Invalid distribution JSON
    res_invalid = client.get(
        f"/v1/cases/{case_version_id}/consensus-divergence",
        params={"distribution_json": "not-json"},
    )
    assert res_invalid.status_code == 400


def test_expert_public_gap_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    res = client.get(f"/v1/cases/{case_version_id}/expert-public-gap")
    assert res.status_code == 200
    data = res.json()
    assert data["case_version_id"] == case_version_id
    assert "gap_classification" in data
    assert "gap_magnitude_points" in data
    assert "key_divergence_drivers" in data
    assert "epistemic_bridges" in data


def test_incentive_map_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    res = client.get(f"/v1/cases/{case_version_id}/incentive-map")
    assert res.status_code == 200
    data = res.json()
    assert data["case_version_id"] == case_version_id
    assert "map_id" in data
    assert "alignment_index" in data
    assert "perverse_incentive_risk" in data
    assert "incentive_nodes" in data
    assert len(data["incentive_nodes"]) > 0


def test_normative_models_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    res = client.get(f"/v1/cases/{case_version_id}/normative-models")
    assert res.status_code == 200
    data = res.json()
    assert data["case_version_id"] == case_version_id
    assert "evaluations" in data
    assert len(data["evaluations"]) >= 2
    assert "philosophies_explained_tr" in data
    assert "philosophies_explained_en" in data


def test_perspective_clusters_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    res = client.get(f"/v1/cases/{case_version_id}/perspective-clusters")
    assert res.status_code == 200
    data = res.json()
    assert data["case_version_id"] == case_version_id
    assert data["total_arguments_clustered"] == 1000
    assert len(data["clusters"]) == 3


def test_policy_simulations_get_and_evaluate_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    # GET default
    res = client.get(f"/v1/cases/{case_version_id}/policy-simulations")
    assert res.status_code == 200
    data = res.json()
    assert data["policy_knob_name"] == "Toplu Taşıma Sübvansiyon Oranı"
    assert data["knob_value"] == 50.0

    # POST evaluate
    eval_res = client.post(
        f"/v1/cases/{case_version_id}/policy-simulations/evaluate",
        json={"policy_knob_name": "Karbon Vergisi", "knob_value": 75.0},
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["policy_knob_name"] == "Karbon Vergisi"
    assert eval_data["knob_value"] == 75.0
    assert "fiscal_score" in eval_data
    assert "social_score" in eval_data


def test_process_and_responsibility_analysis_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    # Process analysis
    res_proc = client.get(f"/v1/cases/{case_version_id}/process-analysis")
    assert res_proc.status_code == 200
    proc_data = res_proc.json()
    assert proc_data["case_version_id"] == case_version_id
    assert "analysis_id" in proc_data
    assert "current_stage" in proc_data
    assert "procedural_integrity_score" in proc_data
    assert "stages" in proc_data

    # Responsibility analysis
    res_resp = client.get(f"/v1/cases/{case_version_id}/responsibility-analysis")
    assert res_resp.status_code == 200
    resp_data = res_resp.json()
    assert resp_data["case_version_id"] == case_version_id
    assert "analysis_id" in resp_data
    assert "clarity_score" in resp_data
    assert "actor_allocations" in resp_data


def test_segment_and_stakeholder_distributions_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"
    # Segment distributions
    res_seg = client.get(f"/v1/cases/{case_version_id}/segment-distributions")
    assert res_seg.status_code == 200
    seg_data = res_seg.json()
    assert seg_data["case_version_id"] == case_version_id
    assert "minimum_sample_threshold" in seg_data
    assert "segments" in seg_data
    assert "privacy_guarantees" in seg_data

    # Stakeholder distributions
    res_stk = client.get(f"/v1/cases/{case_version_id}/stakeholder-distributions")
    assert res_stk.status_code == 200
    stk_data = res_stk.json()
    assert stk_data["case_version_id"] == case_version_id
    assert "total_stakeholders_represented" in stk_data
    assert "stakeholder_distributions" in stk_data
    assert "pluralism_score" in stk_data
