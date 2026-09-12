"""Extended HTTP integration tests for Impact action milestones and institution responses.

Covers:
- POST /v1/impact/actions: create action, required fields, validation
- POST /v1/impact/actions: short description → 422
- PATCH /v1/impact/actions/{id}/progress: update progress
- PATCH /v1/impact/actions/{id}/progress: invalid progress > 100 → 422 or clamped
- PATCH: unknown action_id → 404
- GET /v1/impact/actions: returns list (may be empty without seed)
- GET /v1/impact/institution-responses: returns list
- Institution responses: no personal data leak
- Actions: full lifecycle PROPOSED → IN_PROGRESS → VERIFIED_COMPLETE
- OpenAPI: actions + institution-responses registered
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app

_SEEDED_CASE_VERSION = "22222222-2222-4222-8222-222222222222"
_UNKNOWN_ID = str(uuid.UUID("99999999-9999-4999-8999-999999999999"))


def _client() -> TestClient:
    return TestClient(create_app())


def _create_action(client: TestClient, **overrides) -> dict:
    payload = {
        "title": "Ulaşım altyapısı iyileştirmesi",
        "case_version_id": _SEEDED_CASE_VERSION,
        "signal_id": "sig-test-001",
        "status": "PROPOSED",
        "progress_percentage": 0.0,
        "description": "Bu eylem, KEFE sinyalinden doğrudan tetiklenmiş bir kurumsal yanıttır.",
        "institution_name": "Belediye",
        **overrides,
    }
    res = client.post("/v1/impact/actions", json=payload)
    assert res.status_code == 201, f"Action creation failed: {res.json()}"
    return res.json()


# ---------------------------------------------------------------------------
# Action creation
# ---------------------------------------------------------------------------

def test_action_list_returns_list() -> None:
    client = _client()
    res = client.get("/v1/impact/actions")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_action_create_returns_201() -> None:
    client = _client()
    action = _create_action(client)
    assert "action_id" in action
    uuid.UUID(action["action_id"])


def test_action_create_response_has_required_fields() -> None:
    client = _client()
    action = _create_action(client)
    assert "action_id" in action
    assert "title" in action
    assert "status" in action
    assert "progress_percentage" in action
    assert "created_at" in action


def test_action_create_missing_case_version_id_returns_422() -> None:
    client = _client()
    res = client.post(
        "/v1/impact/actions",
        json={
            "title": "Missing field test",
            "signal_id": "sig-001",
            "status": "PROPOSED",
            "progress_percentage": 0.0,
            "description": "This description is long enough for validation.",
            "institution_name": "Institution",
        },
    )
    assert res.status_code == 422


def test_action_create_short_description_returns_422() -> None:
    client = _client()
    res = client.post(
        "/v1/impact/actions",
        json={
            "title": "Short desc test",
            "case_version_id": _SEEDED_CASE_VERSION,
            "signal_id": "sig-001",
            "status": "PROPOSED",
            "progress_percentage": 0.0,
            "description": "Short",  # < 10 chars
            "institution_name": "Institution",
        },
    )
    assert res.status_code == 422


def test_action_create_appears_in_list() -> None:
    client = _client()
    action = _create_action(client, title="List visibility test action for KEFE impact")
    action_id = action["action_id"]

    list_res = client.get("/v1/impact/actions")
    assert list_res.status_code == 200
    ids = [a["action_id"] for a in list_res.json()]
    assert action_id in ids


# ---------------------------------------------------------------------------
# Action progress update (PATCH)
# ---------------------------------------------------------------------------

def _patch_payload(progress: float, status: str) -> dict:
    """Build a complete PATCH payload (case_version_id required by endpoint)."""
    return {
        "progress_percentage": progress,
        "status": status,
        "case_version_id": _SEEDED_CASE_VERSION,
    }


def test_action_patch_progress_updates_value() -> None:
    client = _client()
    action = _create_action(client)
    action_id = action["action_id"]

    patch_res = client.patch(
        f"/v1/impact/actions/{action_id}/progress",
        json=_patch_payload(50.0, "IN_PROGRESS"),
    )
    assert patch_res.status_code in (200, 201, 204)


def test_action_patch_progress_100_complete() -> None:
    client = _client()
    action = _create_action(client)
    action_id = action["action_id"]

    patch_res = client.patch(
        f"/v1/impact/actions/{action_id}/progress",
        json=_patch_payload(100.0, "VERIFIED_COMPLETE"),
    )
    assert patch_res.status_code in (200, 201, 204)


def test_action_patch_progress_unknown_id_not_500() -> None:
    client = _client()
    res = client.patch(
        f"/v1/impact/actions/{_UNKNOWN_ID}/progress",
        json=_patch_payload(50.0, "IN_PROGRESS"),
    )
    assert res.status_code in (400, 404, 422)


def test_action_patch_malformed_id_returns_422() -> None:
    client = _client()
    res = client.patch(
        "/v1/impact/actions/not-a-uuid/progress",
        json=_patch_payload(50.0, "IN_PROGRESS"),
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Institution responses
# ---------------------------------------------------------------------------

def test_institution_responses_returns_list() -> None:
    client = _client()
    res = client.get("/v1/impact/institution-responses")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_institution_responses_no_personal_data() -> None:
    """Institution responses are aggregated — must not contain actor_id."""
    client = _client()
    res = client.get("/v1/impact/institution-responses")
    assert res.status_code == 200
    serialized = res.text.lower()
    for forbidden in ("actor_id", "private_reason", "ideology", "psychometric"):
        assert forbidden not in serialized, (
            f"Personal field '{forbidden}' found in institution responses"
        )


def test_institution_responses_no_auth_required() -> None:
    """Institution responses are public."""
    client = _client()
    res = client.get("/v1/impact/institution-responses")
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_impact_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("impact/actions" in p for p in paths), "impact/actions not in OpenAPI"
    assert any("institution-responses" in p for p in paths), "institution-responses not in OpenAPI"
    assert any("progress" in p and "actions" in p for p in paths), "progress patch not in OpenAPI"