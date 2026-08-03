from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.admin_security.source_subscriptions import (
    SecuredRssAtomSubscriptionService,
)
from kefe_api.modules.knowledge.provider_control import (
    ProviderCredentialMode,
    SourceProviderCapability,
)
from kefe_api.modules.knowledge.rss_atom_subscription import (
    RssAtomSubscriptionActivationResult,
    RssAtomSubscriptionManifest,
    RssAtomSubscriptionManifestRegistry,
)
from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionSchedule,
    SourceAcquisitionScheduleState,
)

NOW = datetime(2026, 8, 3, 15, 0, tzinfo=UTC)
SUBSCRIPTION_CODE = "test.admin_subscription.v1"
ADAPTER_CODE = "test.admin_provider.v1"


def _manifest(**overrides) -> RssAtomSubscriptionManifest:
    values = {
        "subscription_code": SUBSCRIPTION_CODE,
        "adapter_code": ADAPTER_CODE,
        "external_locator": "https://feeds.example.test/news.xml",
        "interval_seconds": 300,
        "max_dispatch_attempts": 3,
        "quota_limit": 20,
        "quota_window_seconds": 60,
        "failure_threshold": 3,
        "circuit_open_seconds": 30,
        "permit_ttl_seconds": 30,
        "connect_timeout_ms": 500,
        "read_timeout_ms": 1500,
        "total_timeout_ms": 2500,
        "max_redirect_hops": 1,
        "terms_evidence_ref": "docref://providers/example/terms-v1",
        "rate_limit_evidence_ref": "evidence://providers/example/rate-v1",
        "locale": "en-US",
        "jurisdiction_code": "US",
    }
    values.update(overrides)
    return RssAtomSubscriptionManifest(**values)


class RecordingActivation:
    def __init__(self, manifest: RssAtomSubscriptionManifest) -> None:
        self.manifest = manifest
        self.calls: list[dict[str, object]] = []

    def activate(
        self,
        *,
        subscription_code: str,
        first_due_at: datetime,
        activated_at: datetime,
    ) -> RssAtomSubscriptionActivationResult:
        self.calls.append(
            {
                "subscription_code": subscription_code,
                "first_due_at": first_due_at,
                "activated_at": activated_at,
            }
        )
        capability = SourceProviderCapability.create(
            adapter_code=self.manifest.adapter_code,
            credential_mode=ProviderCredentialMode.PUBLIC,
            secret_ref=None,
            quota_limit=self.manifest.quota_limit,
            quota_window_seconds=self.manifest.quota_window_seconds,
            failure_threshold=self.manifest.failure_threshold,
            circuit_open_seconds=self.manifest.circuit_open_seconds,
            permit_ttl_seconds=self.manifest.permit_ttl_seconds,
            created_at=activated_at,
        )
        schedule = SourceAcquisitionSchedule(
            id=uuid4(),
            schedule_key="a" * 64,
            adapter_code=self.manifest.adapter_code,
            external_locator=self.manifest.external_locator,
            pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
            pipeline_version="1.0.0",
            configuration_hash=self.manifest.configuration_hash,
            interval_seconds=self.manifest.interval_seconds,
            max_dispatch_attempts=self.manifest.max_dispatch_attempts,
            state=SourceAcquisitionScheduleState.ACTIVE,
            next_due_at=first_due_at,
            created_at=activated_at,
            updated_at=activated_at,
            locale=self.manifest.locale,
            jurisdiction_code=self.manifest.jurisdiction_code,
        )
        return RssAtomSubscriptionActivationResult(
            subscription_code=self.manifest.subscription_code,
            adapter_code=self.manifest.adapter_code,
            provider_capability=capability,
            schedule=schedule,
        )


def _issue_admin(
    app,
    *roles: AdminRole,
    step_up: bool = False,
) -> tuple[TestClient, UUID, str]:
    store = app.state.admin_session_store
    assert isinstance(store, InMemoryAdminSessionStore)
    subject_id = uuid4()
    store.upsert_subject(subject_id, roles=frozenset(roles))
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=NOW,
        mfa_satisfied_at=NOW,
        expires_at=NOW + timedelta(hours=12),
    )
    if step_up:
        store.record_step_up(issued.session_id, step_up_at=NOW)
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, subject_id, issued.csrf_token


def _install_manifest(app):
    manifest = _manifest()
    registry = RssAtomSubscriptionManifestRegistry((manifest,))
    activation = RecordingActivation(manifest)
    app.state.secured_rss_atom_subscription_service = (
        SecuredRssAtomSubscriptionService(
            registry=registry,
            activation=activation,  # type: ignore[arg-type]
            security=app.state.admin_security_service,
        )
    )
    return manifest, activation


def test_inventory_requires_read_capability_and_is_deterministic_redacted() -> None:
    app = create_app()
    first = _manifest()
    second = _manifest(
        subscription_code="test.admin_subscription_two.v1",
        external_locator="https://alerts.example.test/feed.xml",
    )
    registry = RssAtomSubscriptionManifestRegistry((second, first))
    app.state.secured_rss_atom_subscription_service = (
        SecuredRssAtomSubscriptionService(
            registry=registry,
            activation=RecordingActivation(first),  # type: ignore[arg-type]
            security=app.state.admin_security_service,
        )
    )

    anonymous = TestClient(app).get("/internal/admin/v1/source-subscriptions")
    assert anonymous.status_code == 401

    editor, _, _ = _issue_admin(app, AdminRole.EDITOR)
    denied = editor.get("/internal/admin/v1/source-subscriptions")
    assert denied.status_code == 403
    assert denied.json()["code"] == "ADMIN_FORBIDDEN"

    reviewer, _, _ = _issue_admin(app, AdminRole.REVIEWER)
    response = reviewer.get("/internal/admin/v1/source-subscriptions")
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["subscription_code"] for item in items] == [
        first.subscription_code,
        second.subscription_code,
    ]
    assert set(items[0]) == {
        "subscription_code",
        "adapter_code",
        "external_locator",
        "interval_seconds",
        "max_dispatch_attempts",
        "quota_limit",
        "quota_window_seconds",
        "failure_threshold",
        "circuit_open_seconds",
        "permit_ttl_seconds",
        "connect_timeout_ms",
        "read_timeout_ms",
        "total_timeout_ms",
        "max_redirect_hops",
        "locale",
        "jurisdiction_code",
        "configuration_hash",
    }
    rendered = response.text
    for forbidden in (
        "terms-v1",
        "rate-v1",
        "secret_ref",
        "raw_storage_ref",
        "object_key",
        "authorization",
    ):
        assert forbidden not in rendered


def test_activation_requires_csrf_activation_capability_and_step_up() -> None:
    app = create_app()
    manifest, activation = _install_manifest(app)
    payload = {
        "expected_configuration_hash": manifest.configuration_hash,
        "first_due_at": NOW.isoformat(),
    }
    route = f"/internal/admin/v1/source-subscriptions/{SUBSCRIPTION_CODE}/activate"

    access_admin, _, access_csrf = _issue_admin(app, AdminRole.ACCESS_ADMIN)
    missing_csrf = access_admin.post(route, json=payload)
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"

    no_step_up = access_admin.post(
        route,
        headers={ADMIN_CSRF_HEADER: access_csrf},
        json=payload,
    )
    assert no_step_up.status_code == 403
    assert no_step_up.json()["code"] == "ADMIN_STEP_UP_REQUIRED"

    reviewer, _, reviewer_csrf = _issue_admin(
        app,
        AdminRole.REVIEWER,
        step_up=True,
    )
    no_capability = reviewer.post(
        route,
        headers={ADMIN_CSRF_HEADER: reviewer_csrf},
        json=payload,
    )
    assert no_capability.status_code == 403
    assert no_capability.json()["code"] == "ADMIN_FORBIDDEN"
    assert activation.calls == []


def test_stale_configuration_hash_fails_before_activation_side_effect() -> None:
    app = create_app()
    _, activation = _install_manifest(app)
    admin, _, csrf = _issue_admin(app, AdminRole.ACCESS_ADMIN, step_up=True)

    response = admin.post(
        f"/internal/admin/v1/source-subscriptions/{SUBSCRIPTION_CODE}/activate",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "expected_configuration_hash": f"sha256:{'0' * 64}",
            "first_due_at": NOW.isoformat(),
        },
    )

    assert response.status_code == 409
    assert response.json()["code"] == "SOURCE_SUBSCRIPTION_CONFIGURATION_STALE"
    assert response.json()["meta"]["current_configuration_hash"].startswith(
        "sha256:"
    )
    assert activation.calls == []


def test_activation_delegates_exact_manifest_and_returns_bounded_result() -> None:
    app = create_app()
    manifest, activation = _install_manifest(app)
    admin, _, csrf = _issue_admin(app, AdminRole.ACCESS_ADMIN, step_up=True)

    response = admin.post(
        f"/internal/admin/v1/source-subscriptions/{SUBSCRIPTION_CODE}/activate",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "expected_configuration_hash": manifest.configuration_hash,
            "first_due_at": NOW.isoformat(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "subscription_code",
        "adapter_code",
        "configuration_hash",
        "capability_lifecycle",
        "circuit_state",
        "schedule_id",
        "schedule_state",
        "next_due_at",
    }
    assert body["subscription_code"] == SUBSCRIPTION_CODE
    assert body["configuration_hash"] == manifest.configuration_hash
    assert body["capability_lifecycle"] == "ENABLED"
    assert body["circuit_state"] == "CLOSED"
    assert body["schedule_state"] == "ACTIVE"
    assert len(activation.calls) == 1
    assert activation.calls[0]["subscription_code"] == SUBSCRIPTION_CODE
    assert activation.calls[0]["first_due_at"] == NOW
    assert isinstance(activation.calls[0]["activated_at"], datetime)
    for forbidden in (
        "secret_ref",
        "permit_id",
        "terms_evidence_ref",
        "raw_storage_ref",
        "object_key",
    ):
        assert forbidden not in response.text


def test_http_surface_has_no_manifest_mutation_routes() -> None:
    app = create_app()
    admin, _, csrf = _issue_admin(app, AdminRole.ACCESS_ADMIN, step_up=True)
    base = "/internal/admin/v1/source-subscriptions"

    assert admin.put(base, headers={ADMIN_CSRF_HEADER: csrf}, json={}).status_code in {
        404,
        405,
    }
    delete_response = admin.delete(
        f"{base}/{SUBSCRIPTION_CODE}",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert delete_response.status_code == 404
    assert admin.post(base, headers={ADMIN_CSRF_HEADER: csrf}, json={}).status_code in {
        404,
        405,
    }
    paths = create_app().openapi()["paths"]
    assert base in paths
    assert set(paths[base]) == {"get"}
    assert set(paths[f"{base}/{{subscription_code}}/activate"]) == {"post"}


def test_production_inventory_is_empty_and_startup_remains_dormant() -> None:
    app = create_app()
    reviewer, _, _ = _issue_admin(app, AdminRole.REVIEWER)

    response = reviewer.get("/internal/admin/v1/source-subscriptions")
    assert response.status_code == 200
    assert response.json() == {"items": []}
    assert len(app.state.rss_atom_subscription_registry) == 0
    assert app.state.source_scheduler_repository.plan_due_once(at=NOW) is None
