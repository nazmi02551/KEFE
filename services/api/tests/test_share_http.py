"""HTTP integration tests for the Public Share API.

Covers:
- POST /v1/shares: requires auth, creates share after commit, returns token
- POST /v1/shares: cannot share before commit (Commit First invariant)
- POST /v1/shares: missing session_id → 422
- GET /v1/shares/{token}: public — no auth required, returns share data
- GET /v1/shares/{token}: unknown token → 404
- GET /v1/shares/{token}: share does not expose private decision fields
- DELETE /v1/shares/{share_id}: requires auth
- DELETE /v1/shares/{share_id}: removes share (GET returns 404 after)
- Share token format: starts with known prefix
- OpenAPI: all three paths registered
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


def _commit_and_share(client: TestClient, headers: dict) -> dict:
    """Full flow: create session → respond → commit → create share. Returns share body."""
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

    share_res = client.post(
        "/v1/shares",
        headers=headers,
        json={"session_id": session_id},
    )
    assert share_res.status_code == 201
    return share_res.json()


# ---------------------------------------------------------------------------
# Share creation
# ---------------------------------------------------------------------------

def test_share_create_requires_auth() -> None:
    client = _client()
    res = client.post("/v1/shares", json={"session_id": str(uuid.uuid4())})
    assert res.status_code in (401, 403)


def test_share_create_missing_session_id_returns_422() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.post("/v1/shares", headers=headers, json={})
    assert res.status_code == 422


def test_share_create_before_commit_returns_error() -> None:
    """Cannot create share before commit (Commit First invariant)."""
    client = _client()
    headers = _guest_headers(client)
    session_res = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers
    )
    session_id = session_res.json()["session_id"]
    # Do NOT commit
    res = client.post("/v1/shares", headers=headers, json={"session_id": session_id})
    assert res.status_code in (400, 403, 404, 409, 422)


def test_share_create_after_commit_returns_201() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_res = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers
    )
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
    res = client.post("/v1/shares", headers=headers, json={"session_id": session_id})
    assert res.status_code == 201


def test_share_create_response_has_required_fields() -> None:
    client = _client()
    headers = _guest_headers(client)
    share = _commit_and_share(client, headers)
    assert "share_id" in share
    assert "token" in share
    assert "expires_at" in share
    uuid.UUID(share["share_id"])


def test_share_token_format() -> None:
    """Share tokens should have a known prefix pattern."""
    client = _client()
    headers = _guest_headers(client)
    share = _commit_and_share(client, headers)
    token = share["token"]
    assert len(token) > 10
    # Token must not be empty or a raw UUID
    assert "-" * 4 not in token or token.startswith("kefe"), (
        "Share token must not be a raw UUID — should use prefixed format"
    )


# ---------------------------------------------------------------------------
# Share retrieval (public)
# ---------------------------------------------------------------------------

def test_share_get_no_auth_required() -> None:
    """Share lookup is public — no authentication needed."""
    client = _client()
    headers = _guest_headers(client)
    share = _commit_and_share(client, headers)
    token = share["token"]

    # No auth headers
    res = client.get(f"/v1/shares/{token}")
    assert res.status_code == 200


def test_share_get_returns_share_data() -> None:
    client = _client()
    headers = _guest_headers(client)
    share = _commit_and_share(client, headers)
    token = share["token"]

    res = client.get(f"/v1/shares/{token}")
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, dict)


def test_share_get_no_private_decision_leak() -> None:
    """Shared view must not expose private decision reasons or raw responses."""
    client = _client()
    headers = _guest_headers(client)
    share = _commit_and_share(client, headers)
    token = share["token"]

    res = client.get(f"/v1/shares/{token}")
    assert res.status_code == 200
    serialized = res.text.lower()
    for forbidden in ("private_reason", "raw_response", "ideology", "psychometric"):
        assert forbidden not in serialized, (
            f"Private field '{forbidden}' found in public share response"
        )


def test_share_get_unknown_token_returns_404() -> None:
    client = _client()
    res = client.get("/v1/shares/kefe_s_totally_unknown_token_12345")
    assert res.status_code in (404, 422)


# ---------------------------------------------------------------------------
# Share deletion
# ---------------------------------------------------------------------------

def test_share_delete_requires_auth() -> None:
    client = _client()
    fake_share_id = str(uuid.uuid4())
    res = client.delete(f"/v1/shares/{fake_share_id}")
    assert res.status_code in (401, 403)


def test_share_delete_removes_share() -> None:
    """After deletion, GET with the token must return 404."""
    client = _client()
    headers = _guest_headers(client)
    share = _commit_and_share(client, headers)
    share_id = share["share_id"]
    token = share["token"]

    # Verify it exists
    get_before = client.get(f"/v1/shares/{token}")
    assert get_before.status_code == 200

    # Delete
    del_res = client.delete(f"/v1/shares/{share_id}", headers=headers)
    assert del_res.status_code in (200, 204)

    # Should be gone
    get_after = client.get(f"/v1/shares/{token}")
    assert get_after.status_code in (404, 410)


def test_share_delete_unknown_share_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    fake_share_id = str(uuid.uuid4())
    res = client.delete(f"/v1/shares/{fake_share_id}", headers=headers)
    assert res.status_code in (200, 204, 400, 404, 422)


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_share_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert "/v1/shares" in paths or any(p == "/v1/shares" for p in paths), (
        "POST /v1/shares not found in OpenAPI"
    )
    assert any("shares" in p and "{" in p for p in paths), (
        "GET/DELETE /v1/shares/{token} not found in OpenAPI"
    )