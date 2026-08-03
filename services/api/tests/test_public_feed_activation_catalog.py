from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_SESSION_COOKIE
from kefe_api.modules.knowledge.provider_control import SourceProviderCapability
from kefe_api.modules.knowledge.provider_http_transport import (
    ProviderAdoptionProfile,
    ProviderHttpMethod,
)
from kefe_api.modules.knowledge.public_feed_activation import (
    PublicFeedActivationDefinition,
)
from kefe_api.modules.knowledge.public_feed_activation_catalog import (
    MANIFEST_SCHEMA_VERSION,
    InMemoryPublicFeedActivationCatalogRepository,
    PublicFeedActivationCatalogEntry,
    canonical_manifest_hash,
    canonical_manifest_json,
)
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile

NOW = datetime(2026, 8, 3, 8, 30, tzinfo=UTC)


def _definition(
    suffix: str = "one",
    *,
    interval_seconds: int = 300,
) -> PublicFeedActivationDefinition:
    adapter_code = f"test.catalog_feed_{suffix}.v1"
    activation_code = f"test.catalog_activation_{suffix}.v1"
    parser = StrictRssAtomParseProfile(
        max_document_bytes=4096,
        max_items=32,
    )
    capability = SourceProviderCapability.create(
        adapter_code=adapter_code,
        secret_ref=None,
        credential_mode="PUBLIC",
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=60,
        permit_ttl_seconds=30,
        created_at=NOW,
    )
    adoption = ProviderAdoptionProfile(
        adapter_code=adapter_code,
        allowed_origins=(f"https://feeds-{suffix}.example.test",),
        allowed_methods=(ProviderHttpMethod.GET,),
        allowed_media_types=parser.accepted_media_types,
        connect_timeout_ms=200,
        read_timeout_ms=500,
        total_timeout_ms=1000,
        max_response_bytes=parser.max_document_bytes,
        max_redirect_hops=1,
        terms_evidence_ref=f"docref://catalog/{suffix}/terms-v1",
        rate_limit_evidence_ref=f"evidence://catalog/{suffix}/rate-v1",
    )
    return PublicFeedActivationDefinition(
        activation_code=activation_code,
        adapter_code=adapter_code,
        external_locator=f"https://feeds-{suffix}.example.test/news.xml",
        adoption_profile=adoption,
        parser_profile=parser,
        capability=capability,
        first_due_at=NOW,
        interval_seconds=interval_seconds,
        max_dispatch_attempts=3,
        locale="en",
        jurisdiction_code="GLOBAL",
    )


def _entry(
    suffix: str = "one",
    *,
    recorded_at: datetime = NOW,
    recorded_by: str | None = None,
    evidence_ref: str | None = None,
    interval_seconds: int = 300,
) -> PublicFeedActivationCatalogEntry:
    return PublicFeedActivationCatalogEntry.from_definition(
        _definition(suffix, interval_seconds=interval_seconds),
        evidence_ref=evidence_ref or f"evidence://catalog/{suffix}/review-v1",
        recorded_by=recorded_by or f"admin:{uuid4()}",
        recorded_at=recorded_at,
    )


def _issue_admin(app, role: AdminRole) -> TestClient:
    store = app.state.admin_session_store
    assert isinstance(store, InMemoryAdminSessionStore)
    subject_id = uuid4()
    store.upsert_subject(subject_id, roles=frozenset({role}))
    now = datetime.now(UTC)
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=12),
    )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client


def test_catalog_entry_is_canonical_immutable_redacted_and_owned_on_read() -> None:
    definition = _definition()
    entry = _entry()

    assert entry.manifest_schema_version == MANIFEST_SCHEMA_VERSION
    assert entry.configuration_hash == definition.configuration_hash
    assert canonical_manifest_hash(entry.manifest_json) == entry.configuration_hash
    assert entry.manifest_json == canonical_manifest_json(definition.configuration_payload)
    assert entry.activation_code not in repr(entry) or "manifest_json=<redacted" in repr(entry)
    assert entry.evidence_ref not in repr(entry)

    first = entry.manifest_payload()
    second = entry.manifest_payload()
    assert first == second
    assert first is not second
    first["activation_code"] = "mutated"
    assert entry.manifest_payload()["activation_code"] == definition.activation_code

    with pytest.raises(FrozenInstanceError):
        entry.manifest_json = "{}"  # type: ignore[misc]


def test_catalog_manifest_rejects_sensitive_fields_and_integrity_drift() -> None:
    for payload in (
        {"authorization": "Bearer private"},
        {"cookie_header": "session=private"},
        {"client_secret": "private"},
        {"secret_ref": "vault://private"},
        {"backend_object_key": "bucket/private"},
    ):
        with pytest.raises(ValueError):
            canonical_manifest_json(payload)

    entry = _entry()
    with pytest.raises(ValueError, match="manifest hash"):
        replace(entry, configuration_hash="sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="canonical JSON"):
        replace(entry, manifest_json="{ \"a\": 1 }")


def test_memory_catalog_is_idempotent_conflict_safe_and_deterministic() -> None:
    first = _entry("one")
    repository = InMemoryPublicFeedActivationCatalogRepository()
    stored = repository.create_or_get(first)

    rerecorded = _entry(
        "one",
        recorded_at=NOW + timedelta(hours=1),
        recorded_by=f"admin:{uuid4()}",
    )
    assert rerecorded.id != stored.id
    assert repository.create_or_get(rerecorded) is stored

    changed_definition = _definition("one", interval_seconds=600)
    conflict = PublicFeedActivationCatalogEntry.from_definition(
        changed_definition,
        evidence_ref=first.evidence_ref,
        recorded_by=f"admin:{uuid4()}",
        recorded_at=NOW,
    )
    with pytest.raises(ValueError, match="conflicting"):
        repository.create_or_get(conflict)

    duplicate_adapter = replace(
        _entry("two"),
        adapter_code=first.adapter_code,
    )
    with pytest.raises(ValueError, match="adapter"):
        repository.create_or_get(duplicate_adapter)

    second = repository.create_or_get(_entry("two"))
    third = repository.create_or_get(_entry("three"))
    expected = sorted((first.activation_code, second.activation_code, third.activation_code))
    assert [item.activation_code for item in repository.list_entries(limit=10)] == expected
    assert [
        item.activation_code
        for item in repository.list_entries(
            limit=10,
            after_activation_code=expected[0],
        )
    ] == expected[1:]
    with pytest.raises(ValueError):
        repository.list_entries(limit=0)


def test_admin_catalog_requires_authentication_and_source_verify() -> None:
    app = create_app()
    repository = app.state.public_feed_activation_catalog_repository
    assert isinstance(repository, InMemoryPublicFeedActivationCatalogRepository)
    repository.create_or_get(_entry())

    anonymous = TestClient(app).get("/internal/admin/v1/public-feed-activations")
    assert anonymous.status_code == 401
    assert anonymous.json()["code"] == "ADMIN_AUTH_REQUIRED"

    editor = _issue_admin(app, AdminRole.EDITOR)
    forbidden = editor.get("/internal/admin/v1/public-feed-activations")
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"
    assert forbidden.json()["meta"]["required_capability"] == "SOURCE_VERIFY"


def test_admin_catalog_list_detail_pagination_and_read_only_method_matrix() -> None:
    app = create_app()
    repository = app.state.public_feed_activation_catalog_repository
    first = repository.create_or_get(_entry("one"))
    second = repository.create_or_get(_entry("two"))
    reviewer = _issue_admin(app, AdminRole.REVIEWER)

    page = reviewer.get(
        "/internal/admin/v1/public-feed-activations",
        params={"limit": 1},
    )
    assert page.status_code == 200
    body = page.json()
    assert len(body["items"]) == 1
    assert body["next_cursor"] == body["items"][0]["activation_code"]
    assert "manifest" not in body["items"][0]
    assert "manifest_json" not in body["items"][0]

    next_page = reviewer.get(
        "/internal/admin/v1/public-feed-activations",
        params={"after_activation_code": body["next_cursor"]},
    )
    assert next_page.status_code == 200
    assert len(next_page.json()["items"]) == 1

    selected = first if first.activation_code == body["items"][0]["activation_code"] else second
    detail = reviewer.get(
        f"/internal/admin/v1/public-feed-activations/{selected.activation_code}"
    )
    assert detail.status_code == 200
    detail_body = detail.json()
    assert detail_body["configuration_hash"] == selected.configuration_hash
    assert detail_body["manifest"]["activation_code"] == selected.activation_code
    assert detail_body["manifest"]["capability"]["secret_ref"] is None
    assert "manifest_json" not in detail_body

    missing = reviewer.get(
        "/internal/admin/v1/public-feed-activations/test.missing_feed.v1"
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "PUBLIC_FEED_ACTIVATION_CATALOG_NOT_FOUND"

    for method in ("post", "put", "patch", "delete"):
        response = getattr(reviewer, method)(
            "/internal/admin/v1/public-feed-activations",
            json={"activation_code": "forbidden"},
        )
        assert response.status_code == 405


def test_production_memory_composition_starts_with_empty_catalog() -> None:
    app = create_app()
    repository = app.state.public_feed_activation_catalog_repository
    assert repository.list_entries(limit=100) == ()
    assert not hasattr(app.state, "public_feed_activation_bundle")
    assert not hasattr(app.state, "public_feed_activation_registry")
