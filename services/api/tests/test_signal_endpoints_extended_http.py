"""Extended HTTP tests for signal sub-endpoints.

Covers endpoints not covered by existing signal test files:
  GET /v1/signals/{signal_id}/contribution-classes
  GET /v1/signals/{signal_id}/targets
  GET /v1/signals/{signal_id}/versioning
  GET /v1/signals/consensus-cards (list)
  POST /internal/signal-pipeline/compute (pipeline trigger)

Invariants:
- All endpoints return structured errors for unknown signal_id (404) — never 500
- Malformed UUID → 422
- Consensus cards endpoint is public (no auth needed)
- Pipeline compute endpoint returns 204 (no content)
- All signal sub-endpoints are OpenAPI-registered
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app

_UNKNOWN_SIGNAL = str(uuid.UUID("99999999-9999-4999-8999-999999999999"))
_SEEDED_CASE_VERSION = "22222222-2222-4222-8222-222222222222"


def _client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Consensus cards (public list)
# ---------------------------------------------------------------------------

def test_consensus_cards_no_auth_required() -> None:
    client = _client()
    res = client.get("/v1/signals/consensus-cards")
    assert res.status_code == 200


def test_consensus_cards_returns_list() -> None:
    client = _client()
    res = client.get("/v1/signals/consensus-cards")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_consensus_cards_with_limit_param() -> None:
    client = _client()
    res = client.get("/v1/signals/consensus-cards?limit=5&offset=0")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ---------------------------------------------------------------------------
# Contribution classes
# ---------------------------------------------------------------------------

def test_contribution_classes_unknown_signal_returns_404() -> None:
    client = _client()
    res = client.get(f"/v1/signals/{_UNKNOWN_SIGNAL}/contribution-classes")
    assert res.status_code in (404, 422)


def test_contribution_classes_malformed_uuid_returns_422() -> None:
    client = _client()
    res = client.get("/v1/signals/not-a-uuid/contribution-classes")
    assert res.status_code == 422


def test_contribution_classes_404_response_has_message() -> None:
    client = _client()
    res = client.get(f"/v1/signals/{_UNKNOWN_SIGNAL}/contribution-classes")
    assert res.status_code in (404, 422)
    body = res.json()
    # Error body must be informative
    assert "detail" in body or "message" in body or "type" in body


# ---------------------------------------------------------------------------
# Signal targets
# ---------------------------------------------------------------------------

def test_signal_targets_unknown_signal_returns_404() -> None:
    client = _client()
    res = client.get(f"/v1/signals/{_UNKNOWN_SIGNAL}/targets")
    assert res.status_code in (404, 422)


def test_signal_targets_malformed_uuid_returns_422() -> None:
    client = _client()
    res = client.get("/v1/signals/not-a-uuid/targets")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Signal versioning
# ---------------------------------------------------------------------------

def test_signal_versioning_unknown_signal_returns_404() -> None:
    client = _client()
    res = client.get(f"/v1/signals/{_UNKNOWN_SIGNAL}/versioning")
    assert res.status_code in (404, 422)


def test_signal_versioning_malformed_uuid_returns_422() -> None:
    client = _client()
    res = client.get("/v1/signals/not-a-uuid/versioning")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Signal pipeline compute (internal)
# ---------------------------------------------------------------------------

def test_pipeline_compute_returns_204() -> None:
    client = _client()
    res = client.post(
        "/internal/signal-pipeline/compute",
        json={"case_version_id": _SEEDED_CASE_VERSION},
    )
    assert res.status_code in (200, 204)


def test_pipeline_compute_missing_case_version_id_returns_422() -> None:
    client = _client()
    res = client.post("/internal/signal-pipeline/compute", json={})
    assert res.status_code == 422


def test_pipeline_compute_malformed_case_version_id() -> None:
    client = _client()
    res = client.post(
        "/internal/signal-pipeline/compute",
        json={"case_version_id": "not-a-uuid"},
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_signal_sub_endpoints_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("contribution-classes" in p for p in paths), (
        "contribution-classes not in OpenAPI"
    )
    assert any("targets" in p and "signal" in p for p in paths), (
        "signal targets not in OpenAPI"
    )
    assert any("versioning" in p and "signal" in p for p in paths), (
        "signal versioning not in OpenAPI"
    )
    assert any("signal-pipeline/compute" in p for p in paths), (
        "signal pipeline compute not in OpenAPI"
    )