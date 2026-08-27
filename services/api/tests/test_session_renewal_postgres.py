from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)

_LEGACY_ACTOR_ID = UUID("cafe0000-0000-4000-8000-000000000001")
_LEGACY_SESSION_ID = UUID("cafe0000-0000-4000-8000-000000000002")


def _app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    app = create_app()
    return app, TestClient(app)


def test_postgres_legacy_bootstrap_survives_restart_and_can_renew(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, client = _app(monkeypatch)
    legacy_access = "kefe_g_postgres-legacy-bootstrap-access"
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.begin() as connection:
        connection.execute(
            text("DELETE FROM identity.actor_session WHERE id = :session_id"),
            {"session_id": _LEGACY_SESSION_ID},
        )
        connection.execute(
            text("DELETE FROM identity.actor WHERE id = :actor_id"),
            {"actor_id": _LEGACY_ACTOR_ID},
        )
        connection.execute(
            text(
                """
                INSERT INTO identity.actor (id, actor_kind, state)
                VALUES (:actor_id, 'GUEST', 'ACTIVE')
                """
            ),
            {"actor_id": _LEGACY_ACTOR_ID},
        )
        connection.execute(
            text(
                """
                INSERT INTO identity.actor_session (
                    id,
                    actor_id,
                    token_hash,
                    expires_at
                )
                VALUES (
                    :session_id,
                    :actor_id,
                    :token_hash,
                    :expires_at
                )
                """
            ),
            {
                "session_id": _LEGACY_SESSION_ID,
                "actor_id": _LEGACY_ACTOR_ID,
                "token_hash": hashlib.sha256(
                    legacy_access.encode("utf-8")
                ).hexdigest(),
                "expires_at": datetime.now(UTC) + timedelta(days=7),
            },
        )

    bootstrap = client.post(
        "/v1/identity/session/continuity/bootstrap",
        headers={"Authorization": f"Bearer {legacy_access}"},
    )
    assert bootstrap.status_code == 200
    initial = bootstrap.json()
    assert initial["actor_id"] == str(_LEGACY_ACTOR_ID)
    assert initial["rotation_counter"] == 0

    get_settings.cache_clear()
    restarted = TestClient(create_app())
    renewed = restarted.post(
        "/v1/identity/session/renew",
        json={"renewal_token": initial["renewal_token"]},
    )
    assert renewed.status_code == 200
    assert renewed.json()["actor_id"] == str(_LEGACY_ACTOR_ID)
    assert renewed.json()["rotation_counter"] == 1

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    rotation_counter,
                    renewal_token_hash,
                    token_derivation_key_id,
                    continuity_absolute_expires_at,
                    continuity_inactive_expires_at
                FROM identity.actor_session
                WHERE id = :session_id
                """
            ),
            {"session_id": _LEGACY_SESSION_ID},
        ).mappings().one()
    assert row["rotation_counter"] == 1
    assert row["renewal_token_hash"] is not None
    assert row["token_derivation_key_id"] is not None
    assert row["continuity_absolute_expires_at"] is not None
    assert row["continuity_inactive_expires_at"] is not None
    get_settings.cache_clear()


def test_postgres_concurrent_same_renewal_token_converges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, client = _app(monkeypatch)
    issued = client.post("/v1/identity/guest", json={"platform": "ANDROID"})
    assert issued.status_code == 201
    initial = issued.json()
    payload = {"renewal_token": initial["renewal_token"]}

    def renew() -> dict[str, object]:
        with TestClient(app) as concurrent_client:
            response = concurrent_client.post(
                "/v1/identity/session/renew",
                json=payload,
            )
            assert response.status_code == 200
            return response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: renew(), range(2)))

    assert results[0] == results[1]
    assert results[0]["actor_id"] == initial["actor_id"]
    assert results[0]["rotation_counter"] == 1

    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.connect() as connection:
        rotation_counter = connection.execute(
            text(
                """
                SELECT rotation_counter
                FROM identity.actor_session
                WHERE actor_id = :actor_id AND revoked_at IS NULL
                """
            ),
            {"actor_id": initial["actor_id"]},
        ).scalar_one()
    assert rotation_counter == 1
    get_settings.cache_clear()
