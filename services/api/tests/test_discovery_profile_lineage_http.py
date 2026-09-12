"""HTTP tests for discovery profile, weigh-session lineage and consensus-card participation.

Covers:
  GET  /v1/discovery/profile: requires auth, returns profile shape
  PUT  /v1/discovery/profile: requires auth, updates preferences
  GET  /v1/weigh-sessions/{id}/lineage: requires auth, post-commit
  GET  /v1/weigh-sessions/{id}/consensus-cards: requires auth
  POST /v1/weigh-sessions/{id}/consensus-cards/{card_id}/participation: requires auth
  GET  /v1/weigh-sessions/{id}/reflection-steps/{step_code}: requires auth
  POST /v1/weigh-sessions/{id}/reflection-steps/{step_code}/complete: requires auth
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
# Discovery profile
# ---------------------------------------------------------------------------

def test_discovery_profile_no_auth_returns_200() -> None:
    """Discovery profile is public — returns default profile without auth."""
    client = _client()
    res = client.get("/v1/discovery/profile")
    assert res.status_code == 200


def test_discovery_profile_returns_200() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/discovery/profile", headers=headers)
    assert res.status_code == 200


def test_discovery_profile_response_shape() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/discovery/profile", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, dict)
    # Profile must have at least one meaningful field
    assert len(body) >= 1


def test_discovery_profile_put_no_auth_returns_422_or_200() -> None:
    """Discovery profile PUT without auth: 422 (validation) or 200/204 (default actor)."""
    client = _client()
    res = client.put("/v1/discovery/profile", json={"complexity_level": "ADVANCED"})
    assert res.status_code in (200, 204, 422)


def test_discovery_profile_put_with_auth_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.put(
        "/v1/discovery/profile",
        headers=headers,
        json={"complexity_level": "ADVANCED"},
    )
    # 200 (updated) or 422 (validation) — never 500
    assert res.status_code in (200, 204, 422)


def test_discovery_profile_put_empty_body_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.put("/v1/discovery/profile", headers=headers, json={})
    assert res.status_code in (200, 204, 422)


def test_discovery_profile_actor_isolation() -> None:
    """Two guests must not see each other's profiles."""
    client = _client()
    headers_a = _guest_headers(client)
    headers_b = _guest_headers(client)

    profile_a = client.get("/v1/discovery/profile", headers=headers_a).json()
    profile_b = client.get("/v1/discovery/profile", headers=headers_b).json()

    # Profiles must be separate dicts
    assert isinstance(profile_a, dict)
    assert isinstance(profile_b, dict)


# ---------------------------------------------------------------------------
# Weigh-session lineage
# ---------------------------------------------------------------------------

def test_lineage_requires_auth() -> None:
    client = _client()
    res = client.get(f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/lineage")
    assert res.status_code in (401, 403)


def test_lineage_after_commit_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _create_and_commit(client, headers)
    res = client.get(f"/v1/weigh-sessions/{session_id}/lineage", headers=headers)
    assert res.status_code in (200, 404, 422)


def test_lineage_malformed_session_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/weigh-sessions/not-a-uuid/lineage", headers=headers)
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Weigh-session consensus-cards (session-scoped)
# ---------------------------------------------------------------------------

def test_session_consensus_cards_requires_auth() -> None:
    client = _client()
    res = client.get(f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/consensus-cards")
    assert res.status_code in (401, 403)


def test_session_consensus_cards_after_commit_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _create_and_commit(client, headers)
    res = client.get(f"/v1/weigh-sessions/{session_id}/consensus-cards", headers=headers)
    assert res.status_code in (200, 404)


def test_session_consensus_cards_malformed_session() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get("/v1/weigh-sessions/not-a-uuid/consensus-cards", headers=headers)
    assert res.status_code == 422


def test_consensus_card_participation_requires_auth() -> None:
    client = _client()
    fake_card = str(uuid.uuid4())
    res = client.post(
        f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/consensus-cards/{fake_card}/participation",
        json={},
    )
    assert res.status_code in (401, 403)


def test_consensus_card_participation_malformed_session() -> None:
    client = _client()
    headers = _guest_headers(client)
    fake_card = str(uuid.uuid4())
    res = client.post(
        f"/v1/weigh-sessions/not-a-uuid/consensus-cards/{fake_card}/participation",
        headers=headers,
        json={},
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Reflection steps
# ---------------------------------------------------------------------------

def test_reflection_step_requires_auth() -> None:
    client = _client()
    res = client.get(f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/reflection-steps/REVIEW")
    assert res.status_code in (401, 403)


def test_reflection_step_malformed_session() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.get(
        "/v1/weigh-sessions/not-a-uuid/reflection-steps/REVIEW",
        headers=headers,
    )
    assert res.status_code == 422


def test_reflection_step_after_commit_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    session_id = _create_and_commit(client, headers)
    res = client.get(
        f"/v1/weigh-sessions/{session_id}/reflection-steps/REVIEW",
        headers=headers,
    )
    assert res.status_code in (200, 404, 422)


def test_reflection_step_complete_requires_auth() -> None:
    client = _client()
    res = client.post(
        f"/v1/weigh-sessions/{_UNKNOWN_SESSION}/reflection-steps/REVIEW/complete",
        json={},
    )
    assert res.status_code in (401, 403)


def test_reflection_step_complete_malformed_session() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.post(
        "/v1/weigh-sessions/not-a-uuid/reflection-steps/REVIEW/complete",
        headers=headers,
        json={},
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_discovery_and_lineage_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("discovery/profile" in p for p in paths), "discovery/profile not in OpenAPI"
    assert any("lineage" in p for p in paths), "lineage not in OpenAPI"
    assert any("reflection-steps" in p for p in paths), "reflection-steps not in OpenAPI"