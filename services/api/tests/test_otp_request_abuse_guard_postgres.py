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
    monkeypatch.setenv("KEFE_OTP_REQUEST_GUARD_MODE", "ENFORCE")
    monkeypatch.setenv("KEFE_OTP_REQUEST_COOLDOWN_SECONDS", "300")
    monkeypatch.setenv("KEFE_OTP_REQUEST_WINDOW_SECONDS", "900")
    monkeypatch.setenv("KEFE_OTP_REQUEST_WINDOW_LIMIT", "5")
    monkeypatch.setenv("KEFE_OTP_REQUEST_GUARD_RETENTION_SECONDS", "86400")
    get_settings.cache_clear()
    app = create_app()
    return app, TestClient(app)


def _identifier_hash(email: str) -> str:
    return hashlib.sha256(f"EMAIL:{email.lower()}".encode()).hexdigest()


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
    code = app.state.otp_delivery.code_for(
        channel=OtpChannel.EMAIL,
        identifier=email,
    )
    assert code is not None
    verified = client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": challenge.json()["challenge_id"], "code": code},
    )
    assert verified.status_code == 200
    return verified.json()["verification_token"]


def test_postgres_guard_survives_application_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = "guard-restart@example.test"
    app, client = _app(monkeypatch)
    first = client.post(
        "/v1/auth/otp/request",
        json={"channel": "EMAIL", "identifier": email},
    )
    assert first.status_code == 201

    get_settings.cache_clear()
    restarted_app = create_app()
    restarted_client = TestClient(restarted_app)
    second = restarted_client.post(
        "/v1/auth/otp/request",
        json={"channel": "EMAIL", "identifier": email.upper()},
    )
    assert second.status_code == 429
    assert second.json()["code"] == "AUTH_RATE_LIMITED"

    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.connect() as connection:
        guard_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.otp_request_guard
                WHERE channel = 'EMAIL' AND identifier_hash = :identifier_hash
                """
            ),
            {"identifier_hash": _identifier_hash(email)},
        ).scalar_one()
        challenge_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.otp_challenge
                WHERE channel = 'EMAIL' AND identifier_hash = :identifier_hash
                """
            ),
            {"identifier_hash": _identifier_hash(email)},
        ).scalar_one()
    assert guard_count == 1
    assert challenge_count == 1
    get_settings.cache_clear()


def test_postgres_concurrent_requests_admit_one_challenge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = "guard-race@example.test"
    app, _ = _app(monkeypatch)

    def submit() -> int:
        with TestClient(app) as client:
            response = client.post(
                "/v1/auth/otp/request",
                json={"channel": "EMAIL", "identifier": email},
            )
            return response.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = sorted(executor.map(lambda _: submit(), range(2)))

    assert statuses == [201, 429]
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.connect() as connection:
        guard_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.otp_request_guard
                WHERE channel = 'EMAIL' AND identifier_hash = :identifier_hash
                """
            ),
            {"identifier_hash": _identifier_hash(email)},
        ).scalar_one()
        challenge_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.otp_challenge
                WHERE channel = 'EMAIL' AND identifier_hash = :identifier_hash
                """
            ),
            {"identifier_hash": _identifier_hash(email)},
        ).scalar_one()
    assert guard_count == 1
    assert challenge_count == 1
    get_settings.cache_clear()


def test_privacy_deletion_cascades_destination_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    email = "guard-privacy@example.test"
    app, client = _app(monkeypatch)
    guest_headers, actor_id = _guest(client)
    verification_token = _verification(app, client, email)
    merged = client.post(
        "/v1/auth/guest-merge",
        headers=guest_headers,
        json={"verification_token": verification_token},
    )
    assert merged.status_code == 200
    account_token = merged.json()["access_token"]

    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.connect() as connection:
        before = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.otp_request_guard
                WHERE identifier_hash = :identifier_hash
                """
            ),
            {"identifier_hash": _identifier_hash(email)},
        ).scalar_one()
    assert before == 1

    deleted = client.delete(
        "/v1/me",
        headers={
            "Authorization": f"Bearer {account_token}",
            "X-KEFE-Delete-Confirm": f"DELETE:{actor_id}",
        },
    )
    assert deleted.status_code == 200

    with engine.connect() as connection:
        after = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.otp_request_guard
                WHERE identifier_hash = :identifier_hash
                """
            ),
            {"identifier_hash": _identifier_hash(email)},
        ).scalar_one()
    assert after == 0
    get_settings.cache_clear()


def test_guard_schema_contains_only_hashes_and_operational_timestamps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app(monkeypatch)
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.connect() as connection:
        columns = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'identity'
                      AND table_name = 'otp_request_guard'
                    """
                )
            ).all()
        }
    assert columns == {
        "channel",
        "identifier_hash",
        "latest_challenge_id",
        "window_started_at",
        "last_requested_at",
        "request_count",
        "retention_expires_at",
        "updated_at",
    }
    assert not {"identifier", "identifier_hint", "code", "code_hash"} & columns
    get_settings.cache_clear()
