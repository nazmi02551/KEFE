from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.router import (
    ADMIN_CSRF_HEADER,
    ADMIN_SESSION_COOKIE,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _seed_subject(database_url: str, role: str) -> UUID:
    subject_id = uuid4()
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO admin_security.subject (id, state)
                VALUES (:subject_id, 'ACTIVE')
                """
            ),
            {"subject_id": subject_id},
        )
        connection.execute(
            text(
                """
                INSERT INTO admin_security.role_assignment (
                    id, subject_id, role, granted_at
                ) VALUES (:id, :subject_id, :role, :granted_at)
                """
            ),
            {
                "id": uuid4(),
                "subject_id": subject_id,
                "role": role,
                "granted_at": datetime.now(UTC),
            },
        )
    return subject_id


def _client(app, subject_id: UUID, *, step_up: bool) -> tuple[TestClient, str]:
    now = datetime.now(UTC)
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=2),
    )
    if step_up:
        app.state.admin_session_store.record_step_up(
            issued.session_id,
            step_up_at=now,
        )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token


def _payload(feed_code: str) -> dict[str, object]:
    return {
        "definition_version": 1,
        "feed_code": feed_code,
        "display_name": "PostgreSQL Restart Feed",
        "adapter_code": f"kefe.public_feed.{feed_code}.v1",
        "external_locator": f"https://feeds.example.test/{feed_code}.xml",
        "connect_timeout_ms": 1000,
        "read_timeout_ms": 2000,
        "total_timeout_ms": 3000,
        "max_response_bytes": 2_000_000,
        "max_redirect_hops": 1,
        "terms_evidence_ref": f"evidence://provider-terms/{feed_code}/v1",
        "rate_limit_evidence_ref": f"evidence://provider-rate/{feed_code}/v1",
        "quota_limit": 10,
        "quota_window_seconds": 60,
        "failure_threshold": 3,
        "circuit_open_seconds": 60,
        "permit_ttl_seconds": 30,
        "interval_seconds": 300,
        "max_dispatch_attempts": 3,
        "language_code": "tr",
        "jurisdiction_code": "TR",
    }


def _runtime_counts(database_url: str, adapter_code: str) -> tuple[int, int]:
    engine = create_engine(database_url)
    with engine.connect() as connection:
        provider_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM knowledge.source_provider_capability
                WHERE adapter_code = :adapter_code
                """
            ),
            {"adapter_code": adapter_code},
        ).scalar_one()
        schedule_count = connection.execute(
            text(
                """
                SELECT count(*)
                FROM knowledge.source_acquisition_schedule
                WHERE adapter_code = :adapter_code
                """
            ),
            {"adapter_code": adapter_code},
        ).scalar_one()
    return int(provider_count), int(schedule_count)


def test_postgres_application_restart_rehydrates_without_reactivation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    monkeypatch.setenv("KEFE_API_VERSION", "0.24.0")
    get_settings.cache_clear()

    creator_id = _seed_subject(database_url, "REVIEWER")
    approver_id = _seed_subject(database_url, "ACCESS_ADMIN")
    activator_id = _seed_subject(database_url, "ACCESS_ADMIN")
    feed_code = f"restart-{uuid4().hex[:10]}"
    payload = _payload(feed_code)
    adapter_code = str(payload["adapter_code"])

    try:
        first_app = create_app()
        creator, creator_csrf = _client(first_app, creator_id, step_up=True)
        approver, approver_csrf = _client(first_app, approver_id, step_up=True)
        activator, activator_csrf = _client(first_app, activator_id, step_up=True)

        created = creator.post(
            "/internal/admin/v1/public-feeds",
            headers={ADMIN_CSRF_HEADER: creator_csrf},
            json=payload,
        )
        assert created.status_code == 201
        configuration_hash = created.json()["configuration_hash"]

        preflight = creator.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/preflight",
            headers={ADMIN_CSRF_HEADER: creator_csrf},
        )
        assert preflight.status_code == 200

        approved = approver.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/approve",
            headers={ADMIN_CSRF_HEADER: approver_csrf},
            json={"expected_configuration_hash": configuration_hash},
        )
        assert approved.status_code == 200

        activated = activator.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/activate",
            headers={ADMIN_CSRF_HEADER: activator_csrf},
            json={
                "expected_configuration_hash": configuration_hash,
                "first_due_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
            },
        )
        assert activated.status_code == 200
        schedule_id = UUID(activated.json()["schedule_id"])
        assert first_app.state.canonical_public_feed_runtime_profiles.adapter_codes() == (
            adapter_code,
        )
        assert _runtime_counts(database_url, adapter_code) == (1, 1)

        second_app = create_app()
        assert second_app.state.canonical_public_feed_runtime_profiles.adapter_codes() == (
            adapter_code,
        )
        assert second_app.state.public_capture_registry.adapter_codes() == (adapter_code,)
        assert second_app.state.source_scheduler_repository.get_schedule(schedule_id) is not None
        assert _runtime_counts(database_url, adapter_code) == (1, 1)

        reader, _reader_csrf = _client(second_app, creator_id, step_up=False)
        listed = reader.get("/internal/admin/v1/public-feeds")
        assert listed.status_code == 200
        assert [item["feed_code"] for item in listed.json()["items"]] == [feed_code]
        audit = reader.get(f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/audit")
        assert audit.status_code == 200
        assert [item["action"] for item in audit.json()["items"]] == [
            "DRAFT_REGISTERED",
            "PREFLIGHT_SUCCEEDED",
            "APPROVED",
            "ACTIVATED",
        ]
    finally:
        get_settings.cache_clear()
