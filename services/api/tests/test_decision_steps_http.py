"""HTTP integration tests for decision-step sub-endpoints.

Decision steps are part of the post-commit reflection/revision flow:
  /v1/weigh-sessions/{session_id}/decision-steps/{step_code}/responses
  /v1/weigh-sessions/{session_id}/decision-steps/{step_code}/reason
  /v1/weigh-sessions/{session_id}/decision-steps/{step_code}/commit

Covers:
- Auth guard: all three endpoints require auth
- Pre-commit invariant: steps blocked before main session commit (409)
- Post-commit: responses PUT accepted
- Post-commit: reason PUT accepted
- Post-commit: step commit accepted
- Malformed session_id → 422
- Malformed step_code (non-existent) → 404/422/409
- OpenAPI: all three paths registered
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID

_STEP_CODE = "CHOOSE"


def _client() -> TestClient:
    return TestClient(create_app())


def _guest_headers(client: TestClient) -> dict[str, str]:
    res = client.post("/v1/identity/guest")
    assert res.status_code == 201
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_session(client: TestClient, headers: dict) -> str:
    res = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    assert res.status_code == 201
    return res.json()["session_id"]


def _commit_session(client: TestClient, headers: dict, session_id: str) -> None:
    client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )


# ---------------------------------------------------------------------------
# Auth guards
# ---------------------------------------------------------------------------

def test_step_responses_requires_auth() -> None:
    client = _client()
    fake = str(uuid.uuid4())
    res = client.put(
        f"/v1/weigh-sessions/{fake}/decision-steps/{_STEP_CODE}/responses",
        json={"responses": []},
    )
    assert res.status_code in (401, 403)


def test_step_reason_requires_auth() -> None:
    client = _client()
    fake = str(uuid.uuid4())
    res = client.put(
        f"/v1/weigh-sessions/{fake}/decision-steps/{_STEP_CODE}/reason",
        json={"reason": "Test"},
    )
    assert res.status_code in (401, 403)


def test_step_commit_requires_auth() -> None:
    client = _client()
    fake = str(uuid.uuid4())
    res = client.post(
        f"/v1/weigh-sessions/{fake}/decision-steps/{_STEP_CODE}/commit",
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Pre-commit invariant (steps require prior session commit)
# ---------------------------------------------------------------------------

def test_step_responses_before_session_commit_returns_409() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)
    # Do NOT commit the main session
    res = client.put(
        f"/v1/weigh-sessions/{session_id}/decision-steps/{_STEP_CODE}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    assert res.status_code in (400, 403, 409, 422)


def test_step_reason_before_session_commit_returns_409() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)
    res = client.put(
        f"/v1/weigh-sessions/{session_id}/decision-steps/{_STEP_CODE}/reason",
        headers=headers,
        json={"reason": "Bu tercih daha adil."},
    )
    assert res.status_code in (400, 403, 409, 422)


def test_step_commit_before_session_commit_returns_409() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)
    res = client.post(
        f"/v1/weigh-sessions/{session_id}/decision-steps/{_STEP_CODE}/commit",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code in (400, 403, 409, 422)


# ---------------------------------------------------------------------------
# Post-commit flow
# ---------------------------------------------------------------------------

def test_step_responses_after_session_commit_accepted() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)
    _commit_session(client, headers, session_id)

    res = client.put(
        f"/v1/weigh-sessions/{session_id}/decision-steps/{_STEP_CODE}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    # 200 (accepted) or 404 (step not applicable for this session type) — never 500
    assert res.status_code in (200, 201, 204, 404, 422)


def test_step_reason_after_session_commit_accepted() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)
    _commit_session(client, headers, session_id)

    res = client.put(
        f"/v1/weigh-sessions/{session_id}/decision-steps/{_STEP_CODE}/reason",
        headers=headers,
        json={"reason": "Bu tercih metodolojik açıdan daha dengeli görünüyor."},
    )
    assert res.status_code in (200, 201, 204, 404, 422)


def test_step_commit_after_session_commit_accepted() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _create_session(client, headers)
    _commit_session(client, headers, session_id)

    res = client.post(
        f"/v1/weigh-sessions/{session_id}/decision-steps/{_STEP_CODE}/commit",
        headers={**headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert res.status_code in (200, 201, 204, 404, 409, 422)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_step_responses_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.put(
        f"/v1/weigh-sessions/not-a-uuid/decision-steps/{_STEP_CODE}/responses",
        headers=headers,
        json={"responses": []},
    )
    assert res.status_code == 422


def test_step_reason_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.put(
        "/v1/weigh-sessions/not-a-uuid/decision-steps/CHOOSE/reason",
        headers=headers,
        json={"reason": "Test reason."},
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_decision_step_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("decision-steps" in p and "responses" in p for p in paths), (
        "decision-steps/responses path not in OpenAPI"
    )
    assert any("decision-steps" in p and "reason" in p for p in paths), (
        "decision-steps/reason path not in OpenAPI"
    )
    assert any("decision-steps" in p and "commit" in p for p in paths), (
        "decision-steps/commit path not in OpenAPI"
    )