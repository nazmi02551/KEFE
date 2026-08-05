from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta

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

OLD_SECRET = "old-postgres-replay-secret-01234567890123456789"
NEW_SECRET = "new-postgres-replay-secret-01234567890123456789"


def _configure_keyring(
    monkeypatch: pytest.MonkeyPatch,
    *,
    active_key_id: str,
    active_secret: str,
    retained_keys: dict[str, str] | None = None,
) -> None:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    monkeypatch.setenv("KEFE_ACCOUNT_MERGE_REPLAY_ACTIVE_KEY_ID", active_key_id)
    monkeypatch.setenv("KEFE_ACCOUNT_MERGE_REPLAY_SECRET", active_secret)
    monkeypatch.setenv(
        "KEFE_ACCOUNT_MERGE_REPLAY_RETAINED_KEYS",
        json.dumps(retained_keys or {}),
    )
    get_settings.cache_clear()


def _app(
    monkeypatch: pytest.MonkeyPatch,
    *,
    active_key_id: str,
    active_secret: str,
    retained_keys: dict[str, str] | None = None,
):
    _configure_keyring(
        monkeypatch,
        active_key_id=active_key_id,
        active_secret=active_secret,
        retained_keys=retained_keys,
    )
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


def test_postgres_rotation_replays_old_result_after_restart_and_issues_new_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, client = _app(
        monkeypatch,
        active_key_id="old-2026",
        active_secret=OLD_SECRET,
    )
    headers, actor_id = _guest(client)
    verification_token = _verification(
        app,
        client,
        "postgres-rotation-old@example.test",
    )
    assert verification_token.startswith("kefe_v2.old-2026.")
    payload = {"verification_token": verification_token}
    first = client.post("/v1/auth/guest-merge", headers=headers, json=payload)
    assert first.status_code == 200

    restarted_app, restarted_client = _app(
        monkeypatch,
        active_key_id="new-2026",
        active_secret=NEW_SECRET,
        retained_keys={"old-2026": OLD_SECRET},
    )
    replay = restarted_client.post(
        "/v1/auth/guest-merge",
        headers=headers,
        json=payload,
    )
    assert replay.status_code == 200
    assert replay.json() == first.json()

    new_headers, new_actor_id = _guest(restarted_client)
    new_verification = _verification(
        restarted_app,
        restarted_client,
        "postgres-rotation-new@example.test",
    )
    assert new_verification.startswith("kefe_v2.new-2026.")
    new_result = restarted_client.post(
        "/v1/auth/guest-merge",
        headers=new_headers,
        json={"verification_token": new_verification},
    )
    assert new_result.status_code == 200
    assert new_result.json()["actor_id"] == new_actor_id
    assert new_result.json()["access_token"] != first.json()["access_token"]

    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.connect() as connection:
        replay_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.guest_merge_replay
                WHERE source_actor_id IN (:old_actor_id, :new_actor_id)
                """
            ),
            {"old_actor_id": actor_id, "new_actor_id": new_actor_id},
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
        persisted_hashes = set(
            connection.execute(
                text(
                    """
                    SELECT token_hash
                    FROM identity.actor_session
                    WHERE actor_id IN (:old_actor_id, :new_actor_id)
                      AND revoked_at IS NULL
                    """
                ),
                {"old_actor_id": actor_id, "new_actor_id": new_actor_id},
            ).scalars()
        )

    assert replay_count == 2
    assert "credential_key_id" not in replay_columns
    assert "replay_secret" not in replay_columns
    assert "access_token" not in replay_columns
    assert hashlib.sha256(first.json()["access_token"].encode()).hexdigest() in persisted_hashes
    assert hashlib.sha256(new_result.json()["access_token"].encode()).hexdigest() in persisted_hashes
    get_settings.cache_clear()


def test_postgres_live_replay_missing_retained_key_fails_closed_then_expires(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, client = _app(
        monkeypatch,
        active_key_id="old-retire",
        active_secret=OLD_SECRET,
    )
    headers, actor_id = _guest(client)
    verification_token = _verification(
        app,
        client,
        "postgres-retirement@example.test",
    )
    payload = {"verification_token": verification_token}
    first = client.post("/v1/auth/guest-merge", headers=headers, json=payload)
    assert first.status_code == 200

    _, unsafe_client = _app(
        monkeypatch,
        active_key_id="new-retire",
        active_secret=NEW_SECRET,
    )
    missing = unsafe_client.post(
        "/v1/auth/guest-merge",
        headers=headers,
        json=payload,
    )
    assert missing.status_code == 503
    assert missing.json()["code"] == "DEPENDENCY_TEMPORARILY_UNAVAILABLE"
    assert missing.json()["retryable"] is True

    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    expired_at = datetime.now(UTC) - timedelta(seconds=1)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE identity.guest_merge_replay
                SET account_session_expires_at = :expired_at
                WHERE source_actor_id = :actor_id
                """
            ),
            {"actor_id": actor_id, "expired_at": expired_at},
        )
        connection.execute(
            text(
                """
                UPDATE identity.actor_session
                SET expires_at = :expired_at
                WHERE actor_id = :actor_id AND revoked_at IS NULL
                """
            ),
            {"actor_id": actor_id, "expired_at": expired_at},
        )

    expired = unsafe_client.post(
        "/v1/auth/guest-merge",
        headers=headers,
        json=payload,
    )
    assert expired.status_code == 401
    assert expired.json()["code"] == "AUTH_TOKEN_EXPIRED"
    get_settings.cache_clear()
