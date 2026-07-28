from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.modules.admin_http.app import create_admin_app
from kefe_api.modules.admin_http.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.admin_security.content_authoring import SecuredContentAuthoringService
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_authoring.in_memory import InMemoryContentAuthoringRepository
from kefe_api.modules.content_authoring.registry import default_authoring_registry
from kefe_api.modules.content_authoring.service import ContentAuthoringService


def _harness():
    store = InMemoryAdminSessionStore()
    repository = InMemoryContentAuthoringRepository()
    security = AdminSecurityService(
        session_resolver=store,
        policy=default_admin_security_policy(),
    )
    authoring = ContentAuthoringService(repository, default_authoring_registry())
    secured = SecuredContentAuthoringService(
        authoring=authoring,
        repository=repository,
        security=security,
    )
    app = create_admin_app(
        security=security,
        csrf_verifier=store,
        authoring=secured,
    )
    app.state.admin_session_store = store
    return TestClient(app), store, repository


def _session(store: InMemoryAdminSessionStore, *roles: AdminRole):
    now = datetime.now(UTC)
    subject_id = uuid4()
    store.provision_subject(subject_id)
    for role in roles:
        store.grant_role(subject_id, role)
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=1),
    )
    return subject_id, issued


def _cookies(token: str) -> dict[str, str]:
    return {ADMIN_SESSION_COOKIE: token}


def _headers(csrf: str) -> dict[str, str]:
    return {ADMIN_CSRF_HEADER: csrf}


def _case_payload() -> dict:
    issue_id = uuid4()
    question_id = uuid4()
    return {
        "slug": f"admin-http-{uuid4().hex[:10]}",
        "version": {
            "title": "Admin HTTP test Case",
            "summary": "A low-risk authoring boundary test.",
            "base_format_code": "DILEMMA",
            "primary_domain_code": "DAILY_LIFE",
            "content_risk": "L0",
            "issues": [
                {
                    "id": str(issue_id),
                    "code": "PRIMARY_ISSUE",
                    "title": "Primary issue",
                    "sort_order": 0,
                    "questions": [
                        {
                            "id": str(question_id),
                            "stable_code": "PRIMARY_DECISION",
                            "prompt": "Which option?",
                            "response_type": "SINGLE_CHOICE",
                            "response_schema": {"options": ["A", "B"]},
                            "is_active": True,
                            "is_required": True,
                            "sort_order": 0,
                        }
                    ],
                }
            ],
            "context_blocks": [],
            "sources": [],
            "modifiers": [],
            "is_fact_bearing": False,
            "is_real_event": False,
            "required_review_modes": [],
            "completed_review_modes": [],
        },
    }


def _create_and_submit(client: TestClient, store: InMemoryAdminSessionStore):
    editor_id, editor = _session(store, AdminRole.EDITOR)
    payload = _case_payload()
    created = client.post(
        "/v1/cases",
        json=payload,
        cookies=_cookies(editor.session_token),
        headers=_headers(editor.csrf_token),
    )
    assert created.status_code == 201
    created_body = created.json()
    version_id = created_body["version_id"]
    case_id = created_body["case_id"]

    submitted = client.post(
        f"/v1/case-versions/{version_id}/submit-review",
        cookies=_cookies(editor.session_token),
        headers=_headers(editor.csrf_token),
    )
    assert submitted.status_code == 200
    assert submitted.json()["state"] == "IN_REVIEW"
    return editor_id, UUID(case_id), UUID(version_id)


def test_consumer_bearer_never_authenticates_admin_and_admin_responses_are_no_store() -> None:
    client, _, repository = _harness()
    response = client.post(
        "/v1/cases",
        json=_case_payload(),
        headers={
            "Authorization": "Bearer consumer-token-that-must-be-ignored",
            ADMIN_CSRF_HEADER: "not-a-valid-csrf-token",
        },
    )

    assert response.status_code == 401
    assert response.json()["code"] == "ADMIN_AUTH_REQUIRED"
    assert response.headers["cache-control"] == "no-store"
    assert repository.list_versions(uuid4()) == ()


def test_state_change_requires_session_bound_csrf_before_authoring_executes() -> None:
    client, store, repository = _harness()
    _, editor = _session(store, AdminRole.EDITOR)

    missing = client.post(
        "/v1/cases",
        json=_case_payload(),
        cookies=_cookies(editor.session_token),
    )
    assert missing.status_code == 403
    assert missing.json()["code"] == "ADMIN_CSRF_INVALID"

    _, other = _session(store, AdminRole.EDITOR)
    crossed = client.post(
        "/v1/cases",
        json=_case_payload(),
        cookies=_cookies(editor.session_token),
        headers=_headers(other.csrf_token),
    )
    assert crossed.status_code == 403
    assert crossed.json()["code"] == "ADMIN_CSRF_INVALID"
    assert repository.list_versions(uuid4()) == ()


def test_admin_http_lifecycle_uses_capabilities_step_up_and_server_audit_identity() -> None:
    client, store, _ = _harness()
    editor_id, case_id, version_id = _create_and_submit(client, store)

    reviewer_id, reviewer = _session(store, AdminRole.REVIEWER)
    approved = client.post(
        f"/v1/case-versions/{version_id}/approve",
        cookies=_cookies(reviewer.session_token),
        headers=_headers(reviewer.csrf_token),
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "APPROVED"

    publisher_id, publisher = _session(store, AdminRole.PUBLISHER)
    denied = client.post(
        f"/v1/case-versions/{version_id}/publish",
        cookies=_cookies(publisher.session_token),
        headers=_headers(publisher.csrf_token),
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == "ADMIN_STEP_UP_REQUIRED"

    store.record_step_up(publisher.session_id, step_up_at=datetime.now(UTC))
    published = client.post(
        f"/v1/case-versions/{version_id}/publish",
        cookies=_cookies(publisher.session_token),
        headers=_headers(publisher.csrf_token),
    )
    assert published.status_code == 200
    assert published.json()["state"] == "PUBLISHED"

    audit = client.get(
        f"/v1/cases/{case_id}/audit",
        cookies=_cookies(publisher.session_token),
    )
    assert audit.status_code == 200
    assert audit.headers["cache-control"] == "no-store"
    actor_refs = [entry["actor_ref"] for entry in audit.json()["items"]]
    assert actor_refs == [
        f"admin:{editor_id}",
        f"admin:{editor_id}",
        f"admin:{reviewer_id}",
        f"admin:{publisher_id}",
    ]


def test_submitter_cannot_self_approve_over_http() -> None:
    client, store, _ = _harness()
    now = datetime.now(UTC)
    subject_id = uuid4()
    store.provision_subject(subject_id)
    store.grant_role(subject_id, AdminRole.EDITOR)
    store.grant_role(subject_id, AdminRole.REVIEWER)
    session = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=1),
    )

    created = client.post(
        "/v1/cases",
        json=_case_payload(),
        cookies=_cookies(session.session_token),
        headers=_headers(session.csrf_token),
    )
    version_id = created.json()["version_id"]
    assert client.post(
        f"/v1/case-versions/{version_id}/submit-review",
        cookies=_cookies(session.session_token),
        headers=_headers(session.csrf_token),
    ).status_code == 200

    self_review = client.post(
        f"/v1/case-versions/{version_id}/approve",
        cookies=_cookies(session.session_token),
        headers=_headers(session.csrf_token),
    )
    assert self_review.status_code == 403
    assert self_review.json()["code"] == "ADMIN_SEPARATION_OF_DUTIES"


def test_client_cannot_override_admin_identity_or_roles_in_create_payload() -> None:
    client, store, _ = _harness()
    _, editor = _session(store, AdminRole.EDITOR)
    payload = _case_payload()
    payload["actor_ref"] = "admin:forged"
    payload["role"] = "PUBLISHER"

    response = client.post(
        "/v1/cases",
        json=payload,
        cookies=_cookies(editor.session_token),
        headers=_headers(editor.csrf_token),
    )
    assert response.status_code == 422


def test_admin_application_has_no_login_endpoint_or_consumer_docs_surface() -> None:
    client, _, _ = _harness()
    assert client.post("/v1/login").status_code == 404
    assert client.get("/openapi.json").status_code == 404
    assert client.get("/docs").status_code == 404
