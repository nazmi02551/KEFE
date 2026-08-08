from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from kefe_api.modules.health.router import router


def _client_with_probe(probe) -> TestClient:
    app = FastAPI()
    app.state.readiness_probe = probe
    app.include_router(router)
    return TestClient(app)


def test_health_is_liveness_only() -> None:
    client = _client_with_probe(lambda: (_ for _ in ()).throw(RuntimeError("db down")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_succeeds_when_dependencies_are_ready() -> None:
    client = _client_with_probe(lambda: None)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_fails_closed_without_leaking_dependency_details() -> None:
    def failed_probe() -> None:
        raise RuntimeError("postgresql://user:super-secret@database.internal/kefe")

    client = _client_with_probe(failed_probe)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "not ready"}
    assert "super-secret" not in response.text


def test_ready_is_not_added_to_public_openapi_contract() -> None:
    client = _client_with_probe(lambda: None)

    schema = client.get("/openapi.json").json()

    assert "/health" in schema["paths"]
    assert "/ready" not in schema["paths"]
