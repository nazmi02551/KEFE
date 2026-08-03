from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE


def _issue_admin(
    app,
    *roles: AdminRole,
    step_up: bool = False,
) -> tuple[TestClient, UUID, str, str]:
    store = app.state.admin_session_store
    assert isinstance(store, InMemoryAdminSessionStore)
    subject_id = uuid4()
    store.upsert_subject(subject_id, roles=frozenset(roles))
    now = datetime.now(UTC)
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=12),
    )
    if step_up:
        store.record_step_up(issued.session_id, step_up_at=now)
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, subject_id, issued.session_token, issued.csrf_token


def _payload(**overrides) -> dict[str, object]:
    values: dict[str, object] = {
        "feed_code": "test.admin_catalog_feed.v1",
        "display_name": "Admin Catalog Feed",
        "adapter_code": "test.admin_catalog_rss.v1",
        "external_locator": "https://admin-catalog.example.test/feed.xml",
        "parser_profile": {
            "accepted_media_types": [
                "application/atom+xml",
                "application/rss+xml",
                "application/xml",
                "text/xml",
            ],
            "max_document_bytes": 1_048_576,
            "max_elements": 4096,
            "max_depth": 16,
            "max_items": 256,
            "max_node_text_chars": 16_384,
            "max_total_text_chars": 262_144,
            "max_attributes_per_element": 8,
            "max_total_attribute_chars": 65_536,
            "max_metadata_field_chars": 4096,
        },
        "connect_timeout_ms": 1000,
        "read_timeout_ms": 1500,
        "total_timeout_ms": 3000,
        "max_response_bytes": 1_048_576,
        "max_redirect_hops": 2,
        "terms_evidence_ref": "evidence://terms/admin-catalog-v1",
        "rate_limit_evidence_ref": "evidence://rate/admin-catalog-v1",
        "quota_limit": 20,
        "quota_window_seconds": 60,
        "failure_threshold": 3,
        "circuit_open_seconds": 120,
        "permit_ttl_seconds": 30,
        "language_code": "en",
        "jurisdiction_code": "GLOBAL",
    }
    values.update(overrides)
    return values


def test_catalog_routes_require_admin_session_and_source_manage() -> None:
    app = create_app()
    anonymous = TestClient(app)
    assert anonymous.get("/internal/admin/v1/public-feeds").status_code == 401

    editor, _, _, editor_csrf = _issue_admin(app, AdminRole.EDITOR)
    denied_read = editor.get("/internal/admin/v1/public-feeds")
    assert denied_read.status_code == 403
    assert denied_read.json()["code"] == "ADMIN_FORBIDDEN"

    denied_write = editor.post(
        "/internal/admin/v1/public-feeds",
        headers={ADMIN_CSRF_HEADER: editor_csrf},
        json=_payload(),
    )
    assert denied_write.status_code == 403
    assert denied_write.json()["code"] == "ADMIN_FORBIDDEN"
    assert app.state.public_feed_catalog_repository.list_entries() == ()


def test_catalog_mutations_require_same_session_csrf() -> None:
    app = create_app()
    reviewer, _, session_token, csrf = _issue_admin(app, AdminRole.REVIEWER)
    store = app.state.admin_session_store
    before = store.resolve(session_token).principal
    assert before is not None

    missing = reviewer.post(
        "/internal/admin/v1/public-feeds",
        json=_payload(),
    )
    assert missing.status_code == 403
    assert missing.json()["code"] == "ADMIN_CSRF_REQUIRED"
    after_missing = store.resolve(session_token).principal
    assert after_missing is not None
    assert after_missing.last_seen_at == before.last_seen_at

    other, _, _, other_csrf = _issue_admin(app, AdminRole.REVIEWER)
    del other
    cross_session = reviewer.post(
        "/internal/admin/v1/public-feeds",
        headers={ADMIN_CSRF_HEADER: other_csrf},
        json=_payload(),
    )
    assert cross_session.status_code == 403
    assert cross_session.json()["code"] == "ADMIN_CSRF_INVALID"

    valid = reviewer.post(
        "/internal/admin/v1/public-feeds",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_payload(),
    )
    assert valid.status_code == 201
    assert valid.json()["state"] == "REGISTERED"


def test_register_list_detail_audit_and_strict_payload() -> None:
    app = create_app()
    reviewer, subject_id, _, csrf = _issue_admin(app, AdminRole.REVIEWER)

    attacker_payload = _payload(actor_ref="admin:attacker", state="RETIRED")
    rejected = reviewer.post(
        "/internal/admin/v1/public-feeds",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=attacker_payload,
    )
    assert rejected.status_code == 422

    created = reviewer.post(
        "/internal/admin/v1/public-feeds",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_payload(),
    )
    assert created.status_code == 201
    body = created.json()
    entry_id = body["id"]
    assert body["registered_by"] == f"admin:{subject_id}"
    assert body["configuration_hash"].startswith("sha256:")
    assert "session_token" not in body
    assert "csrf_token" not in body

    replay = reviewer.post(
        "/internal/admin/v1/public-feeds",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_payload(),
    )
    assert replay.status_code == 201
    assert replay.json()["id"] == entry_id

    listing = reviewer.get("/internal/admin/v1/public-feeds")
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == [entry_id]

    detail = reviewer.get(f"/internal/admin/v1/public-feeds/{entry_id}")
    assert detail.status_code == 200
    assert detail.json() == body

    audit = reviewer.get(f"/internal/admin/v1/public-feeds/{entry_id}/audit")
    assert audit.status_code == 200
    assert [item["command"] for item in audit.json()["items"]] == ["REGISTER"]
    assert audit.json()["items"][0]["actor_ref"] == f"admin:{subject_id}"


def test_approval_and_retirement_require_fresh_step_up() -> None:
    app = create_app()
    reviewer, subject_id, session_token, csrf = _issue_admin(
        app,
        AdminRole.REVIEWER,
    )
    created = reviewer.post(
        "/internal/admin/v1/public-feeds",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_payload(),
    )
    assert created.status_code == 201
    entry_id = created.json()["id"]

    no_step_up = reviewer.post(
        f"/internal/admin/v1/public-feeds/{entry_id}/approve-manual-capture",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert no_step_up.status_code == 403
    assert no_step_up.json()["code"] == "ADMIN_STEP_UP_REQUIRED"

    principal = app.state.admin_session_store.resolve(session_token).principal
    assert principal is not None
    app.state.admin_session_store.record_step_up(
        principal.session_id,
        step_up_at=datetime.now(UTC),
    )

    approved = reviewer.post(
        f"/internal/admin/v1/public-feeds/{entry_id}/approve-manual-capture",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "MANUAL_CAPTURE_APPROVED"
    assert approved.json()["approved_by"] == f"admin:{subject_id}"

    retired = reviewer.post(
        f"/internal/admin/v1/public-feeds/{entry_id}/retire",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"rationale": "Publisher ownership changed."},
    )
    assert retired.status_code == 200
    assert retired.json()["state"] == "RETIRED"
    assert retired.json()["retired_by"] == f"admin:{subject_id}"
    assert retired.json()["retirement_rationale"] == "Publisher ownership changed."

    audit = reviewer.get("/internal/admin/v1/public-feeds/audit")
    assert audit.status_code == 200
    assert [item["command"] for item in audit.json()["items"]] == [
        "REGISTER",
        "APPROVE_MANUAL_CAPTURE",
        "RETIRE",
    ]

    invalid = reviewer.post(
        f"/internal/admin/v1/public-feeds/{entry_id}/approve-manual-capture",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert invalid.status_code == 409
    assert invalid.json()["code"] == "PUBLIC_FEED_CATALOG_TRANSITION_INVALID"


def test_catalog_detail_returns_not_found_without_mutation() -> None:
    app = create_app()
    reviewer, _, _, _ = _issue_admin(app, AdminRole.REVIEWER)
    missing = reviewer.get(f"/internal/admin/v1/public-feeds/{uuid4()}")
    assert missing.status_code == 404
    assert missing.json()["code"] == "PUBLIC_FEED_CATALOG_NOT_FOUND"
    assert app.state.public_feed_catalog_repository.list_entries() == ()
