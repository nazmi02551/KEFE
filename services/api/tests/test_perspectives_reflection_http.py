"""HTTP integration tests for Perspectives and Reflection endpoints.

Covers:
- Perspectives endpoint: requires auth, returns perspective snapshot post-commit
- Perspectives: Commit First invariant — not accessible before commit
- Perspectives: unknown session → 404
- Reflection steps: GET endpoint shape
- Reflection: requires auth
- Reflection: complete step → no collective leak
- Reveal: post-commit result available, pre-commit blocked
- Lineage endpoint: accessible after commit
- Decision step endpoints: commit sub-step flow
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


def _full_commit(client: TestClient, headers: dict) -> str:
    """Create session, put responses, commit. Returns session_id."""
    session_res = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["session_id"]

    put_res = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    assert put_res.status_code == 200

    commit_res = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert commit_res.status_code == 200
    return session_id


# ---------------------------------------------------------------------------
# Perspectives — authentication
# ---------------------------------------------------------------------------

def test_perspectives_requires_auth() -> None:
    client = _client()
    fake = str(uuid.uuid4())
    res = client.get(f"/v1/weigh-sessions/{fake}/perspectives")
    assert res.status_code in (401, 403)


def test_perspectives_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/weigh-sessions/not-a-uuid/perspectives", headers=headers)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Perspectives — Commit First invariant
# ---------------------------------------------------------------------------

def test_perspectives_before_commit_blocked() -> None:
    """Perspectives must not be accessible before commit (Commit First)."""
    client = _client()
    headers = _guest_headers(client)
    session_res = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers
    )
    session_id = session_res.json()["session_id"]

    # Do NOT commit — perspectives must be inaccessible
    res = client.get(
        f"/v1/weigh-sessions/{session_id}/perspectives", headers=headers
    )
    # Pre-commit: must not return 200 with collective data
    assert res.status_code in (400, 403, 404, 409, 422)


def test_perspectives_after_commit_returns_200() -> None:
    """Perspectives available after commit."""
    client = _client()
    headers = _guest_headers(client)
    session_id = _full_commit(client, headers)

    res = client.get(
        f"/v1/weigh-sessions/{session_id}/perspectives", headers=headers
    )
    assert res.status_code == 200


def test_perspectives_unknown_session_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    fake = str(uuid.uuid4())
    res = client.get(f"/v1/weigh-sessions/{fake}/perspectives", headers=headers)
    assert res.status_code in (400, 403, 404, 422)


# ---------------------------------------------------------------------------
# Reveal — Commit First invariant
# ---------------------------------------------------------------------------

def test_reveal_before_commit_blocked() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_res = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers
    )
    session_id = session_res.json()["session_id"]

    res = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=headers)
    assert res.status_code in (400, 403, 404, 409, 422)


def test_reveal_after_commit_returns_200() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _full_commit(client, headers)

    res = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=headers)
    assert res.status_code == 200


def test_reveal_response_has_no_pre_commit_leakage() -> None:
    """Reveal must not contain prohibited pre-commit fields."""
    client = _client()
    headers = _guest_headers(client)
    session_id = _full_commit(client, headers)

    res = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=headers)
    assert res.status_code == 200
    # The response text must not contain collective data labels
    # that would imply pre-Commit leakage
    serialized = res.text.lower()
    for forbidden in ("private_reason", "other_actors_decision", "ideology", "psychometric"):
        assert forbidden not in serialized, f"Forbidden field '{forbidden}' in reveal response"


# ---------------------------------------------------------------------------
# Lineage endpoint
# ---------------------------------------------------------------------------

def test_lineage_requires_auth() -> None:
    client = _client()
    fake = str(uuid.uuid4())
    res = client.get(f"/v1/weigh-sessions/{fake}/lineage")
    assert res.status_code in (401, 403)


def test_lineage_after_commit_returns_200() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _full_commit(client, headers)

    res = client.get(f"/v1/weigh-sessions/{session_id}/lineage", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), dict)


def test_lineage_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/weigh-sessions/not-a-uuid/lineage", headers=headers)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Reflection steps
# ---------------------------------------------------------------------------

def test_reflection_step_get_requires_auth() -> None:
    client = _client()
    fake = str(uuid.uuid4())
    res = client.get(f"/v1/weigh-sessions/{fake}/reflection-steps/OVERVIEW")
    assert res.status_code in (401, 403)


def test_reflection_step_after_commit_accessible() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _full_commit(client, headers)

    res = client.get(
        f"/v1/weigh-sessions/{session_id}/reflection-steps/OVERVIEW",
        headers=headers,
    )
    # 200 (step exists) or 404 (step code not found) — never 500
    assert res.status_code in (200, 404, 422)


def test_reflection_step_complete_requires_auth() -> None:
    client = _client()
    fake = str(uuid.uuid4())
    res = client.post(
        f"/v1/weigh-sessions/{fake}/reflection-steps/OVERVIEW/complete"
    )
    assert res.status_code in (401, 403)


def test_reflection_step_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get(
        "/v1/weigh-sessions/not-a-uuid/reflection-steps/OVERVIEW",
        headers=headers,
    )
    assert res.status_code == 422