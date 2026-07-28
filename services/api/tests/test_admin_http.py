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


def _valid_case_payload() -> dict[str, object]:
    return {
        "slug": f"admin-http-{uuid4().hex[:10]}",
        "content": {
            "title": "Admin HTTP Case",
            "summary": "Low-risk internal authoring workflow fixture.",
            "base_format_code": "DILEMMA",
            "primary_domain_code": "DAILY_LIFE",
            "content_risk": "L0",
            "issues": [
                {
                    "code": "PRIMARY_ISSUE",
                    "title": "Primary issue",
                    "questions": [
                        {
                            "stable_code": "PRIMARY_DECISION",
                            "prompt": "Which option?",
                            "response_type": "SINGLE_CHOICE",
                            "response_schema": {"options": ["A", "B"]},
                        }
                    ],
                }
            ],
        },
    }


def test_admin_routes_reject_missing_session_and_consumer_token() -> None:
    app = create_app()
    client = TestClient(app)

    missing = client.get("/internal/admin/v1/session")
    assert missing.status_code == 401
    assert missing.json()["code"] == "ADMIN_AUTH_REQUIRED"

    guest = client.post("/v1/identity/guest")
    assert guest.status_code == 201
    client.cookies.set(ADMIN_SESSION_COOKIE, guest.json()["access_token"])

    consumer_token = client.get("/internal/admin/v1/session")
    assert consumer_token.status_code == 401
    assert consumer_token.json()["code"] == "ADMIN_SESSION_INVALID"

    assert client.post("/internal/admin/v1/login").status_code == 404


def test_admin_mutations_require_same_session_csrf_without_extending_invalid_activity() -> None:
    app = create_app()
    client, _, session_token, csrf_token = _issue_admin(app, AdminRole.EDITOR)
    store = app.state.admin_session_store
    before = store.resolve(session_token).principal
    assert before is not None

    missing = client.post("/internal/admin/v1/cases", json=_valid_case_payload())
    assert missing.status_code == 403
    assert missing.json()["code"] == "ADMIN_CSRF_REQUIRED"

    after_missing = store.resolve(session_token).principal
    assert after_missing is not None
    assert after_missing.last_seen_at == before.last_seen_at

    other_client, _, _, other_csrf = _issue_admin(app, AdminRole.EDITOR)
    del other_client
    cross_session = client.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: other_csrf},
        json=_valid_case_payload(),
    )
    assert cross_session.status_code == 403
    assert cross_session.json()["code"] == "ADMIN_CSRF_INVALID"

    valid = client.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: csrf_token},
        json=_valid_case_payload(),
    )
    assert valid.status_code == 201
    body = valid.json()
    assert body["state"] == "DRAFT"
    assert "session_token" not in body
    assert "csrf_token" not in body

    after_valid = store.resolve(session_token).principal
    assert after_valid is not None
    assert after_valid.last_seen_at >= before.last_seen_at


def test_admin_http_lifecycle_uses_server_identity_separation_and_step_up() -> None:
    app = create_app()
    editor, editor_subject, _, editor_csrf = _issue_admin(
        app,
        AdminRole.EDITOR,
        AdminRole.REVIEWER,
    )
    reviewer, reviewer_subject, _, reviewer_csrf = _issue_admin(app, AdminRole.REVIEWER)
    publisher, publisher_subject, _, publisher_csrf = _issue_admin(app, AdminRole.PUBLISHER)

    created = editor.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: editor_csrf},
        json=_valid_case_payload(),
    )
    assert created.status_code == 201
    case_id = created.json()["case_id"]
    version_id = created.json()["id"]

    submitted = editor.post(
        f"/internal/admin/v1/case-versions/{version_id}/submit",
        headers={ADMIN_CSRF_HEADER: editor_csrf},
    )
    assert submitted.status_code == 200
    assert submitted.json()["state"] == "IN_REVIEW"

    self_review = editor.post(
        f"/internal/admin/v1/case-versions/{version_id}/approve",
        headers={ADMIN_CSRF_HEADER: editor_csrf},
    )
    assert self_review.status_code == 403
    assert self_review.json()["code"] == "ADMIN_SEPARATION_OF_DUTIES"

    approved = reviewer.post(
        f"/internal/admin/v1/case-versions/{version_id}/approve",
        headers={ADMIN_CSRF_HEADER: reviewer_csrf},
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "APPROVED"

    stale_step_up = publisher.post(
        f"/internal/admin/v1/case-versions/{version_id}/publish",
        headers={ADMIN_CSRF_HEADER: publisher_csrf},
    )
    assert stale_step_up.status_code == 403
    assert stale_step_up.json()["code"] == "ADMIN_STEP_UP_REQUIRED"

    publisher_session = app.state.admin_session_store.resolve(
        publisher.cookies.get(ADMIN_SESSION_COOKIE)
    ).principal
    assert publisher_session is not None
    app.state.admin_session_store.record_step_up(
        publisher_session.session_id,
        step_up_at=datetime.now(UTC),
    )

    published = publisher.post(
        f"/internal/admin/v1/case-versions/{version_id}/publish",
        headers={ADMIN_CSRF_HEADER: publisher_csrf},
    )
    assert published.status_code == 200
    assert published.json()["state"] == "PUBLISHED"

    audit = reviewer.get(f"/internal/admin/v1/cases/{case_id}/audit")
    assert audit.status_code == 200
    actor_refs = {item["actor_ref"] for item in audit.json()["items"]}
    assert f"admin:{editor_subject}" in actor_refs
    assert f"admin:{reviewer_subject}" in actor_refs
    assert f"admin:{publisher_subject}" in actor_refs
    assert all(value.startswith("admin:") for value in actor_refs)


def test_admin_payload_cannot_supply_audit_or_identity_fields() -> None:
    app = create_app()
    editor, _, _, csrf = _issue_admin(app, AdminRole.EDITOR)
    payload = _valid_case_payload()
    payload["actor_ref"] = "admin:attacker-controlled"

    response = editor.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=payload,
    )
    assert response.status_code == 422

    created = editor.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_valid_case_payload(),
    )
    assert created.status_code == 201
    version_id = created.json()["id"]
    content = _valid_case_payload()["content"]
    assert isinstance(content, dict)
    content["case_id"] = str(uuid4())

    draft_identity_override = editor.put(
        f"/internal/admin/v1/case-versions/{version_id}",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=content,
    )
    assert draft_identity_override.status_code == 422
