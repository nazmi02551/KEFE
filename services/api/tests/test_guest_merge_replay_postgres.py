from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.identity.account_models import OtpChannel

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    app = create_app()
    return app, TestClient(app)


def _guest(client: TestClient) -> tuple[dict[str, str], str]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    body = response.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["actor_id"]


def _verification(app, client: TestClient, email: str) -> str:
    challenge = client.post(
        "/v1/auth/otp/request",
        json={"channel": "EMAIL", "identifier": email},
    )
    assert challenge.status_code == 201
    code = app.state.otp_delivery.code_for(channel=OtpChannel.EMAIL, identifier=email)
    assert code is not None
    verified = client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": challenge.json()["challenge_id"], "code": code},
    )
    assert verified.status_code == 200
    return verified.json()["verification_token"]


def test_postgres_exact_replay_survives_application_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, client = _app(monkeypatch)
    headers, actor_id = _guest(client)
    verification_token = _verification(app, client, "restart-replay@example.test")
    payload = {"verification_token": verification_token}

    first = client.post("/v1/auth/guest-merge", headers=headers, json=payload)
    assert first.status_code == 200

    # Rebuild every service/repository instance while keeping the durable database.
    get_settings.cache_clear()
    restarted_app = create_app()
    restarted_client = TestClient(restarted_app)
    replay = restarted_client.post(
        "/v1/auth/guest-merge",
        headers=headers,
        json=payload,
    )
    assert replay.status_code == 200
    assert replay.json() == first.json()

    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.connect() as connection:
        replay_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.guest_merge_replay
                WHERE source_actor_id = :actor_id
                """
            ),
            {"actor_id": actor_id},
        ).scalar_one()
        active_account_sessions = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.actor_session
                WHERE actor_id = :actor_id AND revoked_at IS NULL
                """
            ),
            {"actor_id": actor_id},
        ).scalar_one()
        persisted_hash = connection.execute(
            text(
                """
                SELECT token_hash
                FROM identity.actor_session
                WHERE actor_id = :actor_id AND revoked_at IS NULL
                """
            ),
            {"actor_id": actor_id},
        ).scalar_one()
        replay_columns = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'identity'
                      AND table_name = 'guest_merge_replay'
                    """
                )
            ).all()
        }

    assert replay_count == 1
    assert active_account_sessions == 1
    assert persisted_hash == hashlib.sha256(
        first.json()["access_token"].encode("utf-8")
    ).hexdigest()
    assert "access_token" not in replay_columns
    assert "verification_token" not in replay_columns
    get_settings.cache_clear()


def test_postgres_concurrent_duplicate_requests_create_one_account_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, bootstrap = _app(monkeypatch)
    headers, actor_id = _guest(bootstrap)
    verification_token = _verification(app, bootstrap, "race-replay@example.test")
    payload = {"verification_token": verification_token}

    def submit() -> dict[str, object]:
        with TestClient(app) as client:
            response = client.post(
                "/v1/auth/guest-merge",
                headers=headers,
                json=payload,
            )
            assert response.status_code == 200
            return response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit(), range(2)))

    assert results[0] == results[1]
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.connect() as connection:
        active_account_sessions = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.actor_session
                WHERE actor_id = :actor_id AND revoked_at IS NULL
                """
            ),
            {"actor_id": actor_id},
        ).scalar_one()
        replay_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.guest_merge_replay
                WHERE source_actor_id = :actor_id
                """
            ),
            {"actor_id": actor_id},
        ).scalar_one()
    assert active_account_sessions == 1
    assert replay_count == 1
    get_settings.cache_clear()
