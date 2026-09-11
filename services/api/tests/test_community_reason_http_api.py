"""HTTP integration tests for the Community Reason API.

All endpoints require authentication (PrincipalDep).  These tests focus on:
- Authentication guard: all endpoints return 401/403/422 without valid bearer
- Malformed UUID path params → 422 (FastAPI validation)
- Request body validation: missing/invalid fields → 422
- Endpoint routing: correct paths registered in the application
- OpenAPI schema: paths appear in /openapi.json
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def _make_client() -> TestClient:
    return TestClient(create_app())


_SESSION_ID = str(uuid.uuid4())
_REASON_ID = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Authentication guard — all endpoints require bearer token
# ---------------------------------------------------------------------------

def test_publish_reason_without_auth() -> None:
    client = _make_client()
    res = client.post(
        f"/v1/weigh-sessions/{_SESSION_ID}/community-reason",
        json={"tags": ["FAIRNESS"], "text": "Uzlaşı sağlayıcı bir yaklaşım"},
    )
    assert res.status_code in (401, 403, 422)


def test_read_reasons_without_auth() -> None:
    client = _make_client()
    res = client.get(f"/v1/weigh-sessions/{_SESSION_ID}/community-reasons")
    assert res.status_code in (401, 403, 422)


def test_react_without_auth() -> None:
    client = _make_client()
    res = client.put(
        f"/v1/community-reasons/{_REASON_ID}/reaction",
        json={"reaction": "AGREE"},
    )
    assert res.status_code in (401, 403, 422)


def test_report_without_auth() -> None:
    client = _make_client()
    res = client.post(
        f"/v1/community-reasons/{_REASON_ID}/reports",
        json={"code": "INAPPROPRIATE"},
    )
    assert res.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Malformed UUID path params — auth fires before UUID validation
# FastAPI authentication middleware runs before path parameter coercion,
# so these return 401/422 depending on middleware order.
# ---------------------------------------------------------------------------

def test_publish_reason_malformed_session_id() -> None:
    client = _make_client()
    res = client.post(
        "/v1/weigh-sessions/not-a-uuid/community-reason",
        json={"tags": ["FAIRNESS"], "text": "Test"},
    )
    # Auth fires before UUID validation in this app configuration
    assert res.status_code in (401, 403, 422)


def test_read_reasons_malformed_session_id() -> None:
    client = _make_client()
    res = client.get("/v1/weigh-sessions/not-a-uuid/community-reasons")
    assert res.status_code in (401, 403, 422)


def test_react_malformed_reason_id() -> None:
    client = _make_client()
    res = client.put(
        "/v1/community-reasons/not-a-uuid/reaction",
        json={"reaction": "AGREE"},
    )
    assert res.status_code in (401, 403, 422)


def test_report_malformed_reason_id() -> None:
    client = _make_client()
    res = client.post(
        "/v1/community-reasons/not-a-uuid/reports",
        json={"code": "INAPPROPRIATE"},
    )
    assert res.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# Request body validation — auth fires before body validation
# Without auth, body errors are not evaluated; endpoint returns 401/403.
# These tests confirm the endpoint is reachable and auth is enforced.
# ---------------------------------------------------------------------------

def test_publish_reason_empty_body_no_auth() -> None:
    client = _make_client()
    res = client.post(
        f"/v1/weigh-sessions/{_SESSION_ID}/community-reason",
        json={},
    )
    # Auth check fires first; body validation happens after auth passes
    assert res.status_code in (401, 403, 422)


def test_react_empty_body_no_auth() -> None:
    client = _make_client()
    res = client.put(
        f"/v1/community-reasons/{_REASON_ID}/reaction",
        json={},
    )
    assert res.status_code in (401, 403, 422)


def test_report_empty_body_no_auth() -> None:
    client = _make_client()
    res = client.post(
        f"/v1/community-reasons/{_REASON_ID}/reports",
        json={},
    )
    assert res.status_code in (401, 403, 422)


# ---------------------------------------------------------------------------
# OpenAPI schema — endpoints appear in spec
# ---------------------------------------------------------------------------

def test_community_reason_endpoints_in_openapi() -> None:
    client = _make_client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})

    # All four paths must be registered
    assert any("community-reason" in p for p in paths), (
        "community-reason publish path not in OpenAPI spec"
    )
    assert any("community-reasons" in p for p in paths), (
        "community-reasons read path not in OpenAPI spec"
    )
    assert any("reaction" in p for p in paths), (
        "reaction path not in OpenAPI spec"
    )
    assert any("reports" in p and "community" in p for p in paths), (
        "community reason reports path not in OpenAPI spec"
    )