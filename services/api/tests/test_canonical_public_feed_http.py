from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.models import (
    AdminCapability,
    AdminRole,
)
from kefe_api.modules.admin_security.router import (
    ADMIN_CSRF_HEADER,
    ADMIN_SESSION_COOKIE,
)


def _client(
    app,
    *,
    roles: frozenset[AdminRole],
    capabilities: frozenset[AdminCapability] = frozenset(),
    step_up: bool = False,
    subject_id: UUID | None = None,
) -> tuple[TestClient, str, UUID]:
    resolved_subject_id = subject_id or uuid4()
    store = app.state.admin_session_store
    store.upsert_subject(
        resolved_subject_id,
        roles=roles,
        capabilities=capabilities,
    )
    now = datetime.now(UTC)
    issued = store.issue(
        admin_subject_id=resolved_subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=2),
    )
    if step_up:
        store.record_step_up(issued.session_id, step_up_at=now)
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token, resolved_subject_id


def _payload(feed_code: str) -> dict[str, object]:
    return {
        "definition_version": 1,
        "feed_code": feed_code,
        "display_name": "Canonical HTTP Feed",
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


def _set_version(monkeypatch: pytest.MonkeyPatch, version: str) -> None:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    monkeypatch.setenv("KEFE_API_VERSION", version)
    get_settings.cache_clear()


def test_canonical_public_feed_routes_are_isolated_to_api_024(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_version(monkeypatch, "0.23.0")
    try:
        app = create_app()
        assert "/internal/admin/v1/public-feeds" not in app.openapi()["paths"]
    finally:
        get_settings.cache_clear()

    _set_version(monkeypatch, "0.24.0")
    try:
        app = create_app()
        paths = app.openapi()["paths"]
        assert "/internal/admin/v1/public-feeds" in paths
        assert (
            "/internal/admin/v1/public-feeds/{feed_code}/versions/"
            "{definition_version}/activate"
        ) in paths
    finally:
        get_settings.cache_clear()


def test_canonical_public_feed_secured_http_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_version(monkeypatch, "0.24.0")
    try:
        app = create_app()
        anonymous = TestClient(app)
        assert anonymous.get("/internal/admin/v1/public-feeds").status_code == 401

        assert app.state.canonical_public_feed_repository.list_definitions() == ()
        assert app.state.canonical_public_feed_runtime_profiles.adapter_codes() == ()
        assert app.state.public_capture_registry.adapter_codes() == ()

        manager, manager_csrf, manager_id = _client(
            app,
            roles=frozenset({AdminRole.REVIEWER}),
            capabilities=frozenset({AdminCapability.SOURCE_APPROVE}),
            step_up=True,
        )
        approver, approver_csrf, approver_id = _client(
            app,
            roles=frozenset({AdminRole.ACCESS_ADMIN}),
            step_up=True,
        )
        feed_code = f"http-{uuid4().hex[:10]}"
        payload = _payload(feed_code)

        missing_csrf = manager.post(
            "/internal/admin/v1/public-feeds",
            json=payload,
        )
        assert missing_csrf.status_code == 403
        assert missing_csrf.json()["error"]["code"] == "ADMIN_CSRF_REQUIRED"

        created = manager.post(
            "/internal/admin/v1/public-feeds",
            headers={ADMIN_CSRF_HEADER: manager_csrf},
            json=payload,
        )
        assert created.status_code == 201
        created_body = created.json()
        definition_hash = created_body["configuration_hash"]
        assert created_body["state"] == "DRAFT"
        assert created_body["created_by_actor_ref"] == f"admin:{manager_id}"

        preflight = manager.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/preflight",
            headers={ADMIN_CSRF_HEADER: manager_csrf},
        )
        assert preflight.status_code == 200
        assert preflight.json()["configuration_hash"] == definition_hash
        assert preflight.json()["allowed_origin"] == "https://feeds.example.test"
        assert app.state.canonical_public_feed_runtime_profiles.adapter_codes() == ()

        self_approval = manager.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/approve",
            headers={ADMIN_CSRF_HEADER: manager_csrf},
            json={"expected_configuration_hash": definition_hash},
        )
        assert self_approval.status_code == 403
        assert self_approval.json()["error"]["code"] == (
            "ADMIN_SEPARATION_OF_DUTIES"
        )

        approved = approver.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/approve",
            headers={ADMIN_CSRF_HEADER: approver_csrf},
            json={"expected_configuration_hash": definition_hash},
        )
        assert approved.status_code == 200
        assert approved.json()["state"] == "APPROVED"
        assert approved.json()["approved_by_actor_ref"] == f"admin:{approver_id}"

        activated = approver.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/activate",
            headers={ADMIN_CSRF_HEADER: approver_csrf},
            json={
                "expected_configuration_hash": definition_hash,
                "first_due_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
            },
        )
        assert activated.status_code == 200
        activation_body = activated.json()
        assert activation_body["state"] == "ACTIVE"
        adapter_code = payload["adapter_code"]
        assert app.state.canonical_public_feed_runtime_profiles.adapter_codes() == (
            adapter_code,
        )
        assert app.state.public_capture_registry.adapter_codes() == (adapter_code,)
        assert (
            app.state.source_scheduler_repository.get_schedule(
                UUID(activation_body["schedule_id"])
            )
            is not None
        )

        paused = approver.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/pause",
            headers={ADMIN_CSRF_HEADER: approver_csrf},
        )
        assert paused.status_code == 200
        assert paused.json()["state"] == "PAUSED"

        resumed = approver.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/resume",
            headers={ADMIN_CSRF_HEADER: approver_csrf},
        )
        assert resumed.status_code == 200
        assert resumed.json()["state"] == "ACTIVE"

        retired_activation = approver.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/retire-activation",
            headers={ADMIN_CSRF_HEADER: approver_csrf},
        )
        assert retired_activation.status_code == 200
        assert retired_activation.json()["state"] == "RETIRED"

        retired_definition = approver.post(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/retire-definition",
            headers={ADMIN_CSRF_HEADER: approver_csrf},
        )
        assert retired_definition.status_code == 200
        assert retired_definition.json()["state"] == "RETIRED"

        listed = manager.get("/internal/admin/v1/public-feeds")
        assert listed.status_code == 200
        assert [item["feed_code"] for item in listed.json()["items"]] == [feed_code]

        audit = manager.get(
            f"/internal/admin/v1/public-feeds/{feed_code}/versions/1/audit"
        )
        assert audit.status_code == 200
        assert [item["action"] for item in audit.json()["items"]] == [
            "DRAFT_REGISTERED",
            "PREFLIGHT_SUCCEEDED",
            "APPROVED",
            "ACTIVATED",
            "PAUSED",
            "RESUMED",
            "ACTIVATION_RETIRED",
            "DEFINITION_RETIRED",
        ]

        rendered = json.dumps(
            {
                "definition": listed.json(),
                "audit": audit.json(),
                "activation": activation_body,
            },
            sort_keys=True,
        ).lower()
        for forbidden in (
            '"payload"',
            '"body"',
            "secret_ref",
            "raw_storage_ref",
            "backend_object_key",
            "authorization",
        ):
            assert forbidden not in rendered
    finally:
        get_settings.cache_clear()
