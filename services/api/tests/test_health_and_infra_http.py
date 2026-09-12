"""HTTP infrastructure tests — health, readiness, docs, OpenAPI spec.

Covers:
- GET /ready: returns 200 with health status
- GET /v1/health (if present): health details
- GET /docs: Swagger UI accessible
- GET /redoc: ReDoc accessible
- GET /openapi.json: valid JSON with paths
- OpenAPI spec has required fields: info, paths, components
- Total route count sanity: at least 80 routes registered
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Readiness probe
# ---------------------------------------------------------------------------

def test_ready_returns_200() -> None:
    client = _client()
    res = client.get("/ready")
    assert res.status_code == 200


def test_ready_response_is_json_or_text() -> None:
    client = _client()
    res = client.get("/ready")
    assert res.status_code == 200
    # Must return some non-empty content
    assert len(res.content) > 0


# ---------------------------------------------------------------------------
# Swagger UI / ReDoc
# ---------------------------------------------------------------------------

def test_docs_accessible() -> None:
    client = _client()
    res = client.get("/docs")
    assert res.status_code == 200
    assert "swagger" in res.text.lower() or "openapi" in res.text.lower()


def test_redoc_accessible() -> None:
    client = _client()
    res = client.get("/redoc")
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# OpenAPI specification
# ---------------------------------------------------------------------------

def test_openapi_json_valid() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    spec = res.json()
    assert "info" in spec
    assert "paths" in spec
    assert isinstance(spec["paths"], dict)
    assert len(spec["paths"]) >= 80, (
        f"Expected at least 80 paths in OpenAPI spec, got {len(spec['paths'])}"
    )


def test_openapi_has_info_fields() -> None:
    client = _client()
    spec = client.get("/openapi.json").json()
    info = spec["info"]
    assert "title" in info
    assert "version" in info


def test_openapi_has_components() -> None:
    client = _client()
    spec = client.get("/openapi.json").json()
    # schemas should be present (Pydantic models)
    assert "components" in spec


def test_openapi_kefe_title_present() -> None:
    client = _client()
    spec = client.get("/openapi.json").json()
    assert "kefe" in spec["info"]["title"].lower(), (
        "KEFE must appear in OpenAPI title"
    )


# ---------------------------------------------------------------------------
# Route count sanity
# ---------------------------------------------------------------------------

def test_total_route_count_sanity() -> None:
    """Ensure the app has at least 100 routes (catches accidental unregistered routers)."""
    from kefe_api.main import create_app as _create
    app = _create()
    route_count = sum(1 for r in app.routes if hasattr(r, "path"))
    assert route_count >= 100, (
        f"Expected at least 100 routes, got {route_count} — router may be missing"
    )