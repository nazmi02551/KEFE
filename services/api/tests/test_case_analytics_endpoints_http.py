"""HTTP integration tests for case analytics sub-endpoints.

Covers endpoints not yet tested:
  GET /v1/cases/{id}/history
  GET /v1/cases/{id}/consensus-divergence
  GET /v1/cases/{id}/expert-public-gap
  GET /v1/cases/{id}/incentive-map
  GET /v1/cases/{id}/normative-models
  GET /v1/cases/{id}/perspective-clusters
  GET /v1/cases/{id}/policy-simulations
  GET /v1/cases/{id}/process-analysis
  GET /v1/cases/{id}/quality-checklist
  GET /v1/cases/{id}/responsibility-analysis
  GET /v1/cases/{id}/stakeholder-distributions
  POST /v1/cases/{id}/policy-simulations/evaluate

Invariants for all:
- Public access (no auth required)
- Seeded case_version_id returns 200 or appropriate empty response
- Unknown case_version_id returns 404 or empty (not 500)
- Malformed UUID returns 422
- No personal/actor data in aggregate responses
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app

_SEEDED_CASE_VERSION = "22222222-2222-4222-8222-222222222222"
_UNKNOWN_VERSION = str(uuid.UUID("99999999-9999-4999-8999-999999999999"))


def _client() -> TestClient:
    return TestClient(create_app())


def _public_sub(client: TestClient, path_suffix: str) -> int:
    """GET a case analytics sub-endpoint (public). Returns status code."""
    url = f"/v1/cases/{_SEEDED_CASE_VERSION}/{path_suffix}"
    res = client.get(url)
    assert res.status_code != 500, f"Server error on {url}: {res.text[:200]}"
    return res.status_code


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def test_case_history_no_auth_required() -> None:
    client = _client()
    status = _public_sub(client, "history")
    assert status in (200, 404)


def test_case_history_unknown_version_not_500() -> None:
    client = _client()
    res = client.get(f"/v1/cases/{_UNKNOWN_VERSION}/history")
    assert res.status_code in (200, 404, 422)


def test_case_history_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/history")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Consensus divergence
# ---------------------------------------------------------------------------

def test_consensus_divergence_accessible() -> None:
    client = _client()
    status = _public_sub(client, "consensus-divergence")
    assert status in (200, 404)


def test_consensus_divergence_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/consensus-divergence")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Expert-public gap
# ---------------------------------------------------------------------------

def test_expert_public_gap_accessible() -> None:
    client = _client()
    status = _public_sub(client, "expert-public-gap")
    assert status in (200, 404)


def test_expert_public_gap_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/expert-public-gap")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Incentive map
# ---------------------------------------------------------------------------

def test_incentive_map_accessible() -> None:
    client = _client()
    status = _public_sub(client, "incentive-map")
    assert status in (200, 404)


def test_incentive_map_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/incentive-map")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Normative models
# ---------------------------------------------------------------------------

def test_normative_models_accessible() -> None:
    client = _client()
    status = _public_sub(client, "normative-models")
    assert status in (200, 404)


def test_normative_models_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/normative-models")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Perspective clusters
# ---------------------------------------------------------------------------

def test_perspective_clusters_accessible() -> None:
    client = _client()
    status = _public_sub(client, "perspective-clusters")
    assert status in (200, 404)


def test_perspective_clusters_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/perspective-clusters")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Policy simulations (GET)
# ---------------------------------------------------------------------------

def test_policy_simulations_accessible() -> None:
    client = _client()
    status = _public_sub(client, "policy-simulations")
    assert status in (200, 404)


def test_policy_simulations_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/policy-simulations")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Policy simulations evaluate (POST)
# ---------------------------------------------------------------------------

def test_policy_simulation_evaluate_missing_body() -> None:
    client = _client()
    res = client.post(
        f"/v1/cases/{_SEEDED_CASE_VERSION}/policy-simulations/evaluate",
        json={},
    )
    assert res.status_code in (200, 201, 204, 400, 404, 422)


def test_policy_simulation_evaluate_malformed_uuid() -> None:
    client = _client()
    res = client.post("/v1/cases/not-a-uuid/policy-simulations/evaluate", json={})
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Process analysis
# ---------------------------------------------------------------------------

def test_process_analysis_accessible() -> None:
    client = _client()
    status = _public_sub(client, "process-analysis")
    assert status in (200, 404)


def test_process_analysis_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/process-analysis")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Quality checklist
# ---------------------------------------------------------------------------

def test_quality_checklist_accessible() -> None:
    client = _client()
    status = _public_sub(client, "quality-checklist")
    assert status in (200, 404)


def test_quality_checklist_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/quality-checklist")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Responsibility analysis
# ---------------------------------------------------------------------------

def test_responsibility_analysis_accessible() -> None:
    client = _client()
    status = _public_sub(client, "responsibility-analysis")
    assert status in (200, 404)


def test_responsibility_analysis_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/responsibility-analysis")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Stakeholder distributions
# ---------------------------------------------------------------------------

def test_stakeholder_distributions_accessible() -> None:
    client = _client()
    status = _public_sub(client, "stakeholder-distributions")
    assert status in (200, 404)


def test_stakeholder_distributions_no_personal_data() -> None:
    client = _client()
    res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/stakeholder-distributions")
    assert res.status_code in (200, 404)
    if res.status_code == 200:
        serialized = res.text.lower()
        for forbidden in ("actor_id", "ideology", "private_reason"):
            assert forbidden not in serialized, (
                f"Personal field '{forbidden}' in stakeholder-distributions"
            )


def test_stakeholder_distributions_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/stakeholder-distributions")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_case_analytics_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    expected = [
        "history", "consensus-divergence", "expert-public-gap", "incentive-map",
        "normative-models", "perspective-clusters", "policy-simulations",
        "process-analysis", "quality-checklist", "responsibility-analysis",
        "stakeholder-distributions",
    ]
    for ep in expected:
        assert any(ep in p for p in paths), f"'{ep}' not found in OpenAPI paths"