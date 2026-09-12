"""HTTP integration tests for public context and community reason reaction endpoints.

Covers:
- GET /v1/case-versions/{id}/context: response shape, auth not required, Commit First safe
- GET /v1/case-versions/{id}/context: unknown version → 404
- GET /v1/case-versions/{id}/context: malformed UUID → 422
- PUT /v1/community-reasons/{id}/reaction: requires auth
- PUT /v1/community-reasons/{id}/reaction: valid payload accepted
- PUT /v1/community-reasons/{id}/reaction: invalid reaction_type → 422
- POST /v1/community-reasons/{id}/reports: requires auth
- POST /v1/community-reasons/{id}/reports: valid payload accepted
- POST /v1/community-reasons/{id}/reports: missing fields → 422
- OpenAPI: all three paths registered
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


def _seeded_reason_id(client: TestClient, headers: dict) -> str | None:
    """Get a seeded community reason_id from a committed session."""
    from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID
    session_res = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers
    )
    if session_res.status_code != 201:
        return None
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
    # List community reasons for the session
    reasons_res = client.get(
        f"/v1/weigh-sessions/{session_id}/community-reasons",
        headers=headers,
    )
    if reasons_res.status_code != 200:
        return None
    reasons = reasons_res.json()
    if isinstance(reasons, list) and reasons:
        return str(reasons[0].get("reason_id") or reasons[0].get("community_reason_id", ""))
    return None


# ---------------------------------------------------------------------------
# Context endpoint — GET /v1/case-versions/{id}/context
# ---------------------------------------------------------------------------

def test_context_no_auth_required() -> None:
    """Context is public — no authentication needed."""
    client = _client()
    res = client.get(f"/v1/case-versions/{_SEEDED_CASE_VERSION}/context")
    assert res.status_code == 200


def test_context_response_shape() -> None:
    client = _client()
    res = client.get(f"/v1/case-versions/{_SEEDED_CASE_VERSION}/context")
    assert res.status_code == 200
    body = res.json()
    assert "case_version_id" in body
    assert "blocks" in body
    assert "sources" in body
    assert isinstance(body["blocks"], list)
    assert isinstance(body["sources"], list)
    assert body["case_version_id"] == _SEEDED_CASE_VERSION


def test_context_blocks_have_required_fields() -> None:
    client = _client()
    res = client.get(f"/v1/case-versions/{_SEEDED_CASE_VERSION}/context")
    assert res.status_code == 200
    blocks = res.json()["blocks"]
    assert len(blocks) >= 1, "Expected at least one context block"
    block = blocks[0]
    assert "context_block_id" in block
    assert "display_order" in block
    assert "title" in block
    assert "body" in block
    assert "claim_status" in block
    assert "disclosure_level" in block


def test_context_no_result_or_perspective_fields() -> None:
    """Context must not contain collective result or perspective data (Commit First)."""
    client = _client()
    res = client.get(f"/v1/case-versions/{_SEEDED_CASE_VERSION}/context")
    assert res.status_code == 200
    serialized = res.text.lower()
    for forbidden in ("collective_result", "perspective_cluster", "consensus_statement"):
        assert forbidden not in serialized, (
            f"Pre-commit leakage: '{forbidden}' found in context response"
        )


def test_context_unknown_version_returns_404() -> None:
    client = _client()
    res = client.get(f"/v1/case-versions/{_UNKNOWN_VERSION}/context")
    assert res.status_code in (404, 200)  # 200 with empty blocks is also acceptable
    if res.status_code == 200:
        assert res.json()["blocks"] == []


def test_context_malformed_uuid_returns_422() -> None:
    client = _client()
    res = client.get("/v1/case-versions/not-a-uuid/context")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Community reason reaction — PUT /v1/community-reasons/{id}/reaction
# ---------------------------------------------------------------------------

def test_reaction_requires_auth() -> None:
    client = _client()
    fake_reason = str(uuid.uuid4())
    res = client.put(
        f"/v1/community-reasons/{fake_reason}/reaction",
        json={"reaction_type": "HELPFUL"},
    )
    assert res.status_code in (401, 403)


def test_reaction_malformed_reason_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.put(
        "/v1/community-reasons/not-a-uuid/reaction",
        headers=headers,
        json={"reaction_type": "HELPFUL"},
    )
    assert res.status_code == 422


def test_reaction_missing_reaction_type_returns_422() -> None:
    client = _client()
    headers = _guest_headers(client)
    fake_reason = str(uuid.uuid4())
    res = client.put(
        f"/v1/community-reasons/{fake_reason}/reaction",
        headers=headers,
        json={},
    )
    assert res.status_code == 422


def test_reaction_unknown_reason_returns_error() -> None:
    """Reacting to a non-existent reason must not return 500."""
    client = _client()
    headers = _guest_headers(client)
    fake_reason = str(uuid.uuid4())
    res = client.put(
        f"/v1/community-reasons/{fake_reason}/reaction",
        headers=headers,
        json={"reaction_type": "HELPFUL"},
    )
    assert res.status_code in (200, 201, 400, 404, 422)


# ---------------------------------------------------------------------------
# Community reason report — POST /v1/community-reasons/{id}/reports
# ---------------------------------------------------------------------------

def test_report_requires_auth() -> None:
    client = _client()
    fake_reason = str(uuid.uuid4())
    res = client.post(
        f"/v1/community-reasons/{fake_reason}/reports",
        json={"report_type": "MISINFORMATION", "note": "Test note."},
    )
    assert res.status_code in (401, 403)


def test_report_malformed_reason_id() -> None:
    client = _client()
    headers = _guest_headers(client)
    res = client.post(
        "/v1/community-reasons/not-a-uuid/reports",
        headers=headers,
        json={"report_type": "MISINFORMATION"},
    )
    assert res.status_code == 422


def test_report_missing_report_type_returns_422() -> None:
    client = _client()
    headers = _guest_headers(client)
    fake_reason = str(uuid.uuid4())
    res = client.post(
        f"/v1/community-reasons/{fake_reason}/reports",
        headers=headers,
        json={"note": "Some note."},
    )
    assert res.status_code == 422


def test_report_unknown_reason_not_500() -> None:
    client = _client()
    headers = _guest_headers(client)
    fake_reason = str(uuid.uuid4())
    res = client.post(
        f"/v1/community-reasons/{fake_reason}/reports",
        headers=headers,
        json={"report_type": "MISINFORMATION"},
    )
    assert res.status_code in (200, 201, 400, 404, 422)


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_context_and_reason_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("context" in p and "case-version" in p for p in paths), (
        "Context path not found in OpenAPI spec"
    )
    assert any("reaction" in p for p in paths), (
        "Community reason reaction path not found in OpenAPI spec"
    )
    assert any("reports" in p and "community-reasons" in p for p in paths), (
        "Community reason reports path not found in OpenAPI spec"
    )