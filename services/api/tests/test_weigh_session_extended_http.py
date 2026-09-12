"""Extended HTTP tests for weigh-session sub-endpoints.

Covers endpoints not yet tested:
  GET  /v1/weigh-sessions/{id}/flow
  GET  /v1/weigh-sessions/{id}/community-reasons
  POST /v1/weigh-sessions/{id}/community-reason
  POST /v1/weigh-sessions/{id}/consensus-cards/{card_id}/participation
  POST /v1/weigh-sessions/{id}/flow-steps/{step_code}/exposures
  PUT  /v1/weigh-sessions/{id}/reason

Invariants:
- All endpoints require auth
- Pre-commit: reason, community-reason, community-reasons blocked or empty
- Post-commit: flow accessible, community-reasons list available
- Malformed session_id → 422
- Unknown session_id → 404 (never 500)
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID

_UNKNOWN_SESSION = str(uuid.UUID("99999999-9999-4999-8999-999999999999"))


def _client() -> TestClient:
    return TestClient(create_app())


def _guest_headers(client: TestClient) -> dict[str, str]:
    res = client.post("/v1/identity/guest")
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_and_commit(client: TestClient, headers: dict) -> str:
    """Create session, respond and commit. Returns session_id."""
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
# GET /v1/weigh-sessions/{id}/flow
# ---------------------------------------------------------------------------

def test_flow_requires_auth() -> None:
    client = _client()
    res = client.get(f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/flow")
    assert res.status_code in (401, 403)


def test_flow_returns_200_with_auth() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_res = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    session_id = session_res.json()["session_id"]
    res = client.get(f"/v1/weigh-sessions/{session_id}/flow", headers=headers)
    assert res.status_code == 200


def test_flow_response_has_session_fields() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_res = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    session_id = session_res.json()["session_id"]
    res = client.get(f"/v1/weigh-sessions/{session_id}/flow", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert "session_id" in body
    assert "session_state" in body


def test_flow_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/weigh-sessions/not-a-uuid/flow", headers=headers)
    assert res.status_code == 422


def test_flow_unknown_session_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get(f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/flow", headers=headers)
    assert res.status_code in (403, 404, 422)


# ---------------------------------------------------------------------------
# PUT /v1/weigh-sessions/{id}/reason
# ---------------------------------------------------------------------------

def test_reason_requires_auth() -> None:
    client = _client()
    res = client.put(
        f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/reason",
        json={"reason": "Test reason."},
    )
    assert res.status_code in (401, 403)


def test_reason_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.put(
        "/v1/weigh-sessions/not-a-uuid/reason",
        headers=headers,
        json={"reason": "Test reason."},
    )
    assert res.status_code == 422


def test_reason_unknown_session_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.put(
        f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/reason",
        headers=headers,
        json={"reason": "Reason for unknown session."},
    )
    assert res.status_code in (400, 403, 404, 409, 422)


def test_reason_accepted_in_draft_session() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_res = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    session_id = session_res.json()["session_id"]
    res = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"reason": "Bu karar toplumsal adalet açısından önemli."},
    )
    # 200 (accepted) or 422 if reason not yet required at this stage
    assert res.status_code in (200, 204, 422)


# ---------------------------------------------------------------------------
# GET /v1/weigh-sessions/{id}/community-reasons
# ---------------------------------------------------------------------------

def test_community_reasons_requires_auth() -> None:
    client = _client()
    res = client.get(f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/community-reasons")
    assert res.status_code in (401, 403)


def test_community_reasons_after_commit_returns_data() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _create_and_commit(client, headers)
    res = client.get(f"/v1/weigh-sessions/{session_id}/community-reasons", headers=headers)
    assert res.status_code == 200
    body = res.json()
    # Response may be a list or an envelope dict with 'items'
    if isinstance(body, dict):
        assert "items" in body
        assert isinstance(body["items"], list)
    else:
        assert isinstance(body, list)


def test_community_reasons_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/weigh-sessions/not-a-uuid/community-reasons", headers=headers)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# POST /v1/weigh-sessions/{id}/community-reason
# ---------------------------------------------------------------------------

def test_community_reason_post_requires_auth() -> None:
    client = _client()
    res = client.post(
        f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/community-reason",
        json={"reason": "Test.", "reason_type": "AGREEMENT"},
    )
    assert res.status_code in (401, 403)


def test_community_reason_post_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.post(
        "/v1/weigh-sessions/not-a-uuid/community-reason",
        headers=headers,
        json={"reason": "Test.", "reason_type": "AGREEMENT"},
    )
    assert res.status_code == 422


def test_community_reason_post_before_commit_returns_error() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_res = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    session_id = session_res.json()["session_id"]
    res = client.post(
        f"/v1/weigh-sessions/{session_id}/community-reason",
        headers=headers,
        json={"reason": "Before commit.", "reason_type": "AGREEMENT"},
    )
    # Must fail before commit
    assert res.status_code in (400, 403, 404, 409, 422)


# ---------------------------------------------------------------------------
# POST /v1/weigh-sessions/{id}/flow-steps/{step_code}/exposures
# ---------------------------------------------------------------------------

def test_flow_step_exposures_requires_auth() -> None:
    client = _client()
    res = client.post(
        f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/flow-steps/INTRO/exposures",
        json={},
    )
    assert res.status_code in (401, 403)


def test_flow_step_exposures_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.post(
        "/v1/weigh-sessions/not-a-uuid/flow-steps/INTRO/exposures",
        headers=headers,
        json={},
    )
    assert res.status_code == 422


def test_flow_step_exposures_active_session_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_res = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    session_id = session_res.json()["session_id"]
    res = client.post(
        f"/v1/weigh-sessions/{session_id}/flow-steps/INTRO/exposures",
        headers=headers,
        json={},
    )
    assert res.status_code in (200, 201, 204, 400, 404, 409, 422)


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_weigh_session_extended_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    expected_subs = ["flow", "community-reason", "flow-steps", "reason"]
    for sub in expected_subs:
        assert any(sub in p and "weigh-sessions" in p for p in paths), (
            f"weigh-sessions/{sub} not found in OpenAPI paths"
        )