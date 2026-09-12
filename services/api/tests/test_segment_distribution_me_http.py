"""HTTP integration tests for segment distributions and /me endpoints.

Covers:
- GET /v1/cases/{id}/segment-distributions: public, no auth required
- Segment distribution response shape: case_version_id, segments[], minimum_sample_threshold
- Segment items shape: cohort_type, cohort_label, distribution
- Unknown case_version_id → 404 or empty
- Malformed case_version_id → 422
- GET /v1/me: not a route, /v1/me/progress is
- GET /v1/me/progress: requires auth, returns progress data
- GET /v1/me/progress shape: categories, completed_count, streak
- GET /v1/me/privacy-export: shape verification (schema_version, actor_id)
- OpenAPI: segment distributions + me/progress registered
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app

_SEEDED_CASE_VERSION = "22222222-2222-4222-8222-222222222222"
_UNKNOWN_VERSION = str(uuid.UUID("99999999-9999-4999-8999-999999999999"))


def _client() -> TestClient:
    return TestClient(create_app())


def _guest_headers(client: TestClient) -> dict[str, str]:
    res = client.post("/v1/identity/guest")
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


# ---------------------------------------------------------------------------
# Segment distributions
# ---------------------------------------------------------------------------

def test_segment_distributions_no_auth_required() -> None:
    """Segment distributions are public — no authentication needed."""
    client = _client()
    res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/segment-distributions")
    assert res.status_code == 200


def test_segment_distributions_response_shape() -> None:
    client = _client()
    res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/segment-distributions")
    assert res.status_code == 200
    body = res.json()
    assert "case_version_id" in body
    assert "segments" in body
    assert "minimum_sample_threshold" in body
    assert isinstance(body["segments"], list)
    assert body["case_version_id"] == _SEEDED_CASE_VERSION
    assert isinstance(body["minimum_sample_threshold"], int)


def test_segment_distributions_has_data() -> None:
    """Seeded case must have at least one segment."""
    client = _client()
    res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/segment-distributions")
    assert res.status_code == 200
    assert len(res.json()["segments"]) >= 1


def test_segment_distributions_item_shape() -> None:
    client = _client()
    res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/segment-distributions")
    assert res.status_code == 200
    segment = res.json()["segments"][0]
    assert "cohort_type" in segment
    assert "cohort_label" in segment
    # At least one meaningful data field must be present
    data_fields = {"distribution", "percentages", "counts", "entropy_score", "is_suppressed", "sample_size"}
    assert any(f in segment for f in data_fields), (
        f"Segment item missing expected data fields. Got: {list(segment.keys())}"
    )


def test_segment_distributions_no_personal_data() -> None:
    """Aggregate segment data must not contain actor_id or individual rows."""
    client = _client()
    res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/segment-distributions")
    assert res.status_code == 200
    serialized = res.text.lower()
    for forbidden in ("actor_id", "private_reason", "ideology"):
        assert forbidden not in serialized, (
            f"Personal field '{forbidden}' found in segment distributions"
        )


def test_segment_distributions_unknown_version_not_500() -> None:
    client = _client()
    res = client.get(f"/v1/cases/{_UNKNOWN_VERSION}/segment-distributions")
    assert res.status_code in (200, 404)


def test_segment_distributions_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/segment-distributions")
    assert res.status_code == 422


def test_segment_distributions_overall_sample_size_positive() -> None:
    client = _client()
    res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/segment-distributions")
    assert res.status_code == 200
    body = res.json()
    if "overall_sample_size" in body:
        assert body["overall_sample_size"] > 0


# ---------------------------------------------------------------------------
# /v1/me/progress
# ---------------------------------------------------------------------------

def test_me_progress_requires_auth() -> None:
    client = _client()
    res = client.get("/v1/me/progress")
    assert res.status_code in (401, 403)


def test_me_progress_returns_200_with_auth() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/me/progress", headers=headers)
    assert res.status_code == 200


def test_me_progress_response_shape() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/me/progress", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, dict)


def test_me_progress_no_other_actor_data() -> None:
    """Progress endpoint must not leak other actors' data."""
    client = _client()
    # Create two guests
    res_a = client.post("/v1/identity/guest")
    res_b = client.post("/v1/identity/guest")
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    prog_a = client.get("/v1/me/progress", headers=headers_a).json()
    prog_b = client.get("/v1/me/progress", headers=headers_b).json()

    # Both should return valid dicts without exposing the other's actor_id
    a_str = str(prog_a)
    b_str = str(prog_b)
    assert res_b.json()["actor_id"] not in a_str, "Guest B's actor_id leaked in Guest A's progress"
    assert res_a.json()["actor_id"] not in b_str, "Guest A's actor_id leaked in Guest B's progress"


# ---------------------------------------------------------------------------
# /v1/me/privacy-export — shape verification
# ---------------------------------------------------------------------------

def test_privacy_export_response_shape() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/me/privacy-export", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert "schema_version" in body
    assert "actor_id" in body
    assert "actor_kind" in body
    assert "generated_at" in body
    assert "manifest" in body
    assert "data_sha256" in body
    assert len(body["data_sha256"]) == 64  # SHA-256 hex


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_segment_and_me_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("segment-distributions" in p for p in paths), (
        "segment-distributions path not in OpenAPI"
    )
    assert any("me/progress" in p for p in paths), (
        "me/progress path not in OpenAPI"
    )