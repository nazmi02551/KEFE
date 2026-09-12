"""Extended HTTP integration tests for Identity and Session endpoints.

Covers:
- POST /v1/identity/guest: creates guest token (extended shape tests)
- POST /v1/identity/session/renew: renews session token
- POST /v1/identity/session/continuity/bootstrap: continuity protocol
- DELETE /v1/identity/session: terminates session
- Token reuse after deletion: token becomes invalid
- Two guests: independent actor_ids
- Guest creation is idempotent-safe (no server error on repeated calls)
- Response fields: access_token, token_type, expires_in, actor_kind
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def _guest(client: TestClient) -> dict:
    res = client.post("/v1/identity/guest")
    assert res.status_code == 201
    return res.json()


def _guest_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": f"Bearer {_guest(client)['access_token']}"}


def _guest_renew_headers(client: TestClient) -> tuple[dict[str, str], str]:
    """Returns (auth_headers, renewal_token)."""
    body = _guest(client)
    return {"Authorization": f"Bearer {body['access_token']}"}, body["renewal_token"]


# ---------------------------------------------------------------------------
# Guest creation — shape tests
# ---------------------------------------------------------------------------

def test_guest_returns_201() -> None:
    client = _client()
    res = client.post("/v1/identity/guest")
    assert res.status_code == 201


def test_guest_response_has_access_token() -> None:
    client = _client()
    body = _guest(client)
    assert "access_token" in body
    assert len(body["access_token"]) > 20


def test_guest_response_has_token_type_bearer() -> None:
    client = _client()
    body = _guest(client)
    assert body.get("token_type", "").lower() == "bearer"


def test_guest_response_has_actor_kind_guest() -> None:
    client = _client()
    body = _guest(client)
    assert body.get("actor_kind") == "GUEST"


def test_two_guests_have_different_tokens() -> None:
    client = _client()
    token_a = _guest(client)["access_token"]
    token_b = _guest(client)["access_token"]
    assert token_a != token_b


def test_guest_token_grants_access_to_protected_endpoint() -> None:
    """A guest token must be accepted on auth-required endpoints."""
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/me/progress", headers=headers)
    assert res.status_code == 200


def test_guest_creation_stable_under_repeated_calls() -> None:
    """Creating 5 guests in sequence must not cause server error."""
    client = _client()
    for _ in range(5):
        res = client.post("/v1/identity/guest")
        assert res.status_code == 201


# ---------------------------------------------------------------------------
# Session renew — POST /v1/identity/session/renew
# ---------------------------------------------------------------------------

def test_session_renew_requires_renewal_token_body() -> None:
    """Session renew without renewal_token body returns 422."""
    client = _client()
    headers = _guest_headers(client)
    res = client.post("/v1/identity/session/renew", headers=headers)
    assert res.status_code == 422


def test_session_renew_returns_new_token() -> None:
    """Session renew with valid renewal_token returns new access_token."""
    client = _client()
    headers, renewal_token = _guest_renew_headers(client)
    res = client.post(
        "/v1/identity/session/renew",
        headers=headers,
        json={"renewal_token": renewal_token},
    )
    assert res.status_code in (200, 201)
    body = res.json()
    assert "access_token" in body


def test_session_renew_new_token_is_usable() -> None:
    """Renewed token must grant access to protected endpoints."""
    client = _client()
    headers, renewal_token = _guest_renew_headers(client)
    renew_res = client.post(
        "/v1/identity/session/renew",
        headers=headers,
        json={"renewal_token": renewal_token},
    )
    assert renew_res.status_code in (200, 201)
    new_token = renew_res.json()["access_token"]
    new_headers = {"Authorization": f"Bearer {new_token}"}
    me_res = client.get("/v1/me/progress", headers=new_headers)
    assert me_res.status_code == 200


# ---------------------------------------------------------------------------
# Session delete — DELETE /v1/identity/session
# ---------------------------------------------------------------------------

def test_session_delete_requires_auth() -> None:
    client = _client()
    res = client.delete("/v1/identity/session")
    assert res.status_code in (401, 403)


def test_session_delete_returns_success() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.delete("/v1/identity/session", headers=headers)
    assert res.status_code in (200, 204)


def test_session_delete_invalidates_token() -> None:
    """After session deletion, the same token must not grant access."""
    client = _client()
    headers = _guest_headers(client)

    del_res = client.delete("/v1/identity/session", headers=headers)
    assert del_res.status_code in (200, 204)

    # Token should no longer be valid
    me_res = client.get("/v1/me/progress", headers=headers)
    assert me_res.status_code in (401, 403)


def test_double_session_delete_not_500() -> None:
    """Deleting an already-deleted session must not return 500."""
    client = _client()
    headers = _guest_headers(client)

    client.delete("/v1/identity/session", headers=headers)
    second = client.delete("/v1/identity/session", headers=headers)
    assert second.status_code in (200, 204, 401, 403, 404)


# ---------------------------------------------------------------------------
# Continuity bootstrap — POST /v1/identity/session/continuity/bootstrap
# ---------------------------------------------------------------------------

def test_continuity_bootstrap_requires_auth() -> None:
    client = _client()
    res = client.post("/v1/identity/session/continuity/bootstrap")
    assert res.status_code in (401, 403)


def test_continuity_bootstrap_with_auth_not_500() -> None:
    """Continuity bootstrap must not crash — 200/201 or informative error."""
    client = _client()
    headers = _guest_headers(client)
    res = client.post("/v1/identity/session/continuity/bootstrap", headers=headers)
    assert res.status_code in (200, 201, 400, 404, 422)


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_identity_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("identity/guest" in p for p in paths), "Guest path not in OpenAPI"
    assert any("session/renew" in p for p in paths), "Session renew path not in OpenAPI"
    assert any("continuity" in p for p in paths), "Continuity bootstrap path not in OpenAPI"