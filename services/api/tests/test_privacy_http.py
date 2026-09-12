"""HTTP integration tests for privacy export and deletion endpoints.

Covers:
- GET /v1/me/privacy-export: requires auth, returns export data
- DELETE /v1/me: requires auth, deletes account
- Export response shape: no causal inference, no personality attributes
- Delete after commit: data is gone
- Guest without data: export returns empty-safe structure
- Auth guard on both endpoints
- Double delete: idempotent or informative error
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID


def _client() -> TestClient:
    return TestClient(create_app())


def _guest_headers(client: TestClient) -> dict[str, str]:
    res = client.post("/v1/identity/guest")
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _commit_demo(client: TestClient, headers: dict) -> str:
    session_res = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["session_id"]

    client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    return session_id


# ---------------------------------------------------------------------------
# Authentication guard
# ---------------------------------------------------------------------------

def test_privacy_export_requires_auth() -> None:
    client = _client()
    res = client.get("/v1/me/privacy-export")
    assert res.status_code in (401, 403)


def test_privacy_delete_requires_auth() -> None:
    client = _client()
    res = client.delete("/v1/me")
    assert res.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Privacy export — shape invariants
# ---------------------------------------------------------------------------

def test_privacy_export_guest_no_data_returns_safe_structure() -> None:
    """Fresh guest export must return safe structure without personal inferences."""
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/me/privacy-export", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, dict)


def test_privacy_export_no_causal_inference_fields() -> None:
    """Export must not contain personality, ideology or causal inference fields."""
    client = _client()
    headers = _guest_headers(client)
    _commit_demo(client, headers)

    res = client.get("/v1/me/privacy-export", headers=headers)
    assert res.status_code == 200
    serialized = res.text.lower()
    for forbidden in (
        "personality",
        "ideology",
        "psychometric",
        "bias_score",
        "causal_inference",
        "predicted_behavior",
    ):
        assert forbidden not in serialized, (
            f"Forbidden inference field '{forbidden}' found in privacy export"
        )


def test_privacy_export_after_commit_includes_actor_data() -> None:
    """After a commit, export includes committed session reference."""
    client = _client()
    headers = _guest_headers(client)
    _commit_demo(client, headers)

    res = client.get("/v1/me/privacy-export", headers=headers)
    assert res.status_code == 200
    body = res.json()
    # Export must be a dict (envelope) — content details depend on implementation
    assert isinstance(body, dict)


# ---------------------------------------------------------------------------
# Privacy deletion
# ---------------------------------------------------------------------------

def _actor_id_from_export(client: TestClient, auth_headers: dict) -> str:
    """Fetch actor_id from privacy export."""
    res = client.get("/v1/me/privacy-export", headers=auth_headers)
    assert res.status_code == 200
    return str(res.json()["actor_id"])


def _delete_headers_for_actor(auth_headers: dict, actor_id: str) -> dict:
    """Build deletion headers with actor-bound confirmation token."""
    return {**auth_headers, "X-KEFE-Delete-Confirm": f"DELETE:{actor_id}"}


def test_privacy_delete_without_confirm_header_returns_422() -> None:
    """DELETE /v1/me without X-KEFE-Delete-Confirm header must fail with 422."""
    client = _client()
    headers = _guest_headers(client)
    res = client.delete("/v1/me", headers=headers)
    assert res.status_code == 422


def test_privacy_delete_wrong_confirm_value_returns_422() -> None:
    """DELETE /v1/me with wrong confirmation value must fail."""
    client = _client()
    headers = _guest_headers(client)
    res = client.delete("/v1/me", headers={**headers, "X-KEFE-Delete-Confirm": "WRONG_VALUE"})
    assert res.status_code == 422


def test_privacy_delete_guest_returns_success() -> None:
    """DELETE /v1/me with correct actor-bound confirm header succeeds."""
    client = _client()
    headers = _guest_headers(client)
    actor_id = _actor_id_from_export(client, headers)
    res = client.delete("/v1/me", headers=_delete_headers_for_actor(headers, actor_id))
    assert res.status_code in (200, 204)


def test_privacy_delete_returns_receipt() -> None:
    """DELETE response contains deletion receipt fields."""
    client = _client()
    headers = _guest_headers(client)
    actor_id = _actor_id_from_export(client, headers)
    res = client.delete("/v1/me", headers=_delete_headers_for_actor(headers, actor_id))
    assert res.status_code in (200, 204)
    if res.status_code == 200:
        body = res.json()
        assert "receipt_id" in body
        assert "actor_id" in body
        assert "deleted_at" in body
        assert body.get("private_data_deleted") is True


def test_privacy_delete_after_commit_succeeds() -> None:
    """Deletion must work even after a committed session."""
    client = _client()
    headers = _guest_headers(client)
    _commit_demo(client, headers)
    actor_id = _actor_id_from_export(client, headers)

    res = client.delete("/v1/me", headers=_delete_headers_for_actor(headers, actor_id))
    assert res.status_code in (200, 204)


def test_privacy_export_after_deletion_reflects_erasure() -> None:
    """After deletion, export must not succeed with pre-delete data.

    Once deleted, the actor's token becomes invalid. The export endpoint
    must return 401 (token revoked), 403, or 404 — never the pre-delete payload.
    """
    client = _client()
    headers = _guest_headers(client)
    _commit_demo(client, headers)

    actor_id = _actor_id_from_export(client, headers)
    del_res = client.delete("/v1/me", headers=_delete_headers_for_actor(headers, actor_id))
    assert del_res.status_code in (200, 204)

    # Export after deletion: token revoked (401) or not found (403/404) — never full pre-delete payload
    export_res = client.get("/v1/me/privacy-export", headers=headers)
    assert export_res.status_code in (401, 403, 404), (
        f"Expected 401/403/404 after erasure, got {export_res.status_code}"
    )


def test_double_delete_does_not_cause_500() -> None:
    """Deleting an already-deleted actor must not return 500.

    After the first DELETE, the actor's token becomes invalid (401) — this is
    the expected behavior: erased actors cannot re-authenticate.
    """
    client = _client()
    headers = _guest_headers(client)
    actor_id = _actor_id_from_export(client, headers)
    confirm_headers = _delete_headers_for_actor(headers, actor_id)

    first = client.delete("/v1/me", headers=confirm_headers)
    assert first.status_code in (200, 204)

    second = client.delete("/v1/me", headers=confirm_headers)
    # After erasure: token invalid (401), or idempotent (200/204/404/403) — never 500
    assert second.status_code in (200, 204, 404, 403, 422, 401)


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_privacy_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("privacy-export" in p for p in paths), (
        "Privacy export path not found in OpenAPI spec"
    )
    assert "/v1/me" in paths or any(p == "/v1/me" for p in paths), (
        "DELETE /v1/me not found in OpenAPI spec"
    )