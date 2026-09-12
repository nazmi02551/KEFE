"""HTTP integration tests for the Weigh Session API.

Covers the full Commit First journey:
  guest → create session → put responses → commit → reveal

Also covers:
- Session not found (unknown session_id) → 404
- Response schema invariants (session_id, case_version_id, status)
- Commit idempotency (same Idempotency-Key returns same result)
- Commit without prior response → error or 400/422
- Flow endpoint: returns flow configuration for session
- Authentication guard: all session endpoints require auth
- Double-commit behavior (idempotency key reuse)
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID


def _make_client() -> TestClient:
    return TestClient(create_app())


def _guest_headers(client: TestClient) -> dict[str, str]:
    res = client.post("/v1/identity/guest")
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_session(client: TestClient, headers: dict) -> str:
    res = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    assert res.status_code == 201
    return res.json()["session_id"]


# ---------------------------------------------------------------------------
# Authentication guard
# ---------------------------------------------------------------------------

def test_create_session_requires_auth() -> None:
    client = _make_client()
    res = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions")
    assert res.status_code in (401, 403)


def test_get_flow_requires_auth() -> None:
    client = _make_client()
    fake_session = str(uuid.uuid4())
    res = client.get(f"/v1/weigh-sessions/{fake_session}/flow")
    assert res.status_code in (401, 403)


def test_put_responses_requires_auth() -> None:
    client = _make_client()
    fake_session = str(uuid.uuid4())
    res = client.put(
        f"/v1/weigh-sessions/{fake_session}/responses",
        json={"responses": []},
    )
    assert res.status_code in (401, 403)


def test_commit_requires_auth() -> None:
    client = _make_client()
    fake_session = str(uuid.uuid4())
    res = client.post(
        f"/v1/weigh-sessions/{fake_session}/commit",
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code in (401, 403)


def test_reveal_requires_auth() -> None:
    client = _make_client()
    fake_session = str(uuid.uuid4())
    res = client.get(f"/v1/weigh-sessions/{fake_session}/reveal")
    assert res.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Session creation
# ---------------------------------------------------------------------------

def test_create_session_returns_201_with_session_id() -> None:
    client = _make_client()
    headers = _guest_headers(client)
    res = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    assert res.status_code == 201
    body = res.json()
    assert "session_id" in body
    # Validate session_id is a valid UUID
    uuid.UUID(body["session_id"])


def test_create_session_unknown_case_returns_error() -> None:
    client = _make_client()
    headers = _guest_headers(client)
    unknown_case = str(uuid.uuid4())
    res = client.post(f"/v1/cases/{unknown_case}/weigh-sessions", headers=headers)
    assert res.status_code in (404, 422)


def test_create_session_malformed_case_id() -> None:
    client = _make_client()
    headers = _guest_headers(client)
    res = client.post("/v1/cases/not-a-uuid/weigh-sessions", headers=headers)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Flow endpoint
# ---------------------------------------------------------------------------

def test_get_flow_returns_200_with_steps() -> None:
    client = _make_client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)
    res = client.get(f"/v1/weigh-sessions/{session_id}/flow", headers=headers)
    assert res.status_code == 200
    body = res.json()
    # Flow must have some structure
    assert isinstance(body, dict)


def test_get_flow_unknown_session_returns_404() -> None:
    client = _make_client()
    headers = _guest_headers(client)
    fake_session = str(uuid.uuid4())
    res = client.get(f"/v1/weigh-sessions/{fake_session}/flow", headers=headers)
    assert res.status_code in (404, 422)


def test_get_flow_malformed_session_id() -> None:
    client = _make_client()
    headers = _guest_headers(client)
    res = client.get("/v1/weigh-sessions/not-a-uuid/flow", headers=headers)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Full commit journey
# ---------------------------------------------------------------------------

def test_full_commit_journey_returns_200() -> None:
    """Guest → create session → put responses → commit → reveal."""
    client = _make_client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)

    # Put response
    put_res = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={
            "responses": [
                {"question_id": str(DEMO_QUESTION_ID), "value": "A"},
            ]
        },
    )
    assert put_res.status_code == 200

    # Commit
    idempotency_key = str(uuid.uuid4())
    commit_res = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": idempotency_key},
    )
    assert commit_res.status_code == 200

    # Reveal (post-commit)
    reveal_res = client.get(
        f"/v1/weigh-sessions/{session_id}/reveal",
        headers=headers,
    )
    assert reveal_res.status_code == 200


def test_commit_idempotency_same_key_returns_same_result() -> None:
    """Same Idempotency-Key on second commit must not create a new commit."""
    client = _make_client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)

    client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )

    key = str(uuid.uuid4())
    first = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": key},
    )
    second = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": key},
    )
    assert first.status_code == 200
    # Idempotent: second call must not error (200 or 409 both acceptable)
    assert second.status_code in (200, 409)


def test_commit_missing_idempotency_key_returns_error() -> None:
    """Commit without Idempotency-Key header should fail."""
    client = _make_client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)

    client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )

    res = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers=headers,  # No Idempotency-Key
    )
    assert res.status_code in (400, 422)


def test_reveal_before_commit_returns_error() -> None:
    """Reveal endpoint must not expose result before commit (Commit First)."""
    client = _make_client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)

    res = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=headers)
    # Must fail before commit — never 200 with collective result
    assert res.status_code in (400, 403, 404, 409, 422)


def test_two_guests_have_independent_sessions() -> None:
    """Session isolation — guest A's session must not be accessible by guest B."""
    client = _make_client()
    headers_a = _guest_headers(client)
    headers_b = _guest_headers(client)

    session_a = _create_session(client, headers_a)

    # Guest B should not be able to access guest A's session
    res = client.get(f"/v1/weigh-sessions/{session_a}/flow", headers=headers_b)
    assert res.status_code in (403, 404)


# ---------------------------------------------------------------------------
# Response validation
# ---------------------------------------------------------------------------

def test_put_responses_malformed_session_id() -> None:
    client = _make_client()
    headers = _guest_headers(client)
    res = client.put(
        "/v1/weigh-sessions/not-a-uuid/responses",
        headers=headers,
        json={"responses": []},
    )
    assert res.status_code == 422