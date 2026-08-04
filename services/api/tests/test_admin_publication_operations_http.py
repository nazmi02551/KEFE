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
) -> tuple[TestClient, UUID, str]:
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
    return client, subject_id, issued.csrf_token


def _create_submit_approve(
    app,
    *,
    title: str,
    content_risk: str = "L1",
    domain: str = "DAILY_LIFE",
    approver_roles: tuple[AdminRole, ...] = (AdminRole.REVIEWER,),
    approver_step_up: bool = False,
) -> tuple[dict[str, object], TestClient, UUID, str]:
    editor, _, editor_csrf = _issue_admin(app, AdminRole.EDITOR)
    reviewer, reviewer_subject, reviewer_csrf = _issue_admin(
        app,
        *approver_roles,
        step_up=approver_step_up,
    )
    created = editor.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: editor_csrf},
        json={
            "slug": f"publication-{uuid4().hex[:10]}",
            "content": {
                "title": title,
                "summary": "Publication operations fixture.",
                "base_format_code": "DILEMMA",
                "primary_domain_code": domain,
                "content_risk": content_risk,
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
                "required_review_modes": [],
                "completed_review_modes": [],
            },
        },
    )
    assert created.status_code == 201
    version = created.json()
    submitted = editor.post(
        f"/internal/admin/v1/case-versions/{version['id']}/submit",
        headers={ADMIN_CSRF_HEADER: editor_csrf},
    )
    assert submitted.status_code == 200
    approved = reviewer.post(
        f"/internal/admin/v1/content-reviews/{version['id']}/decision",
        headers={ADMIN_CSRF_HEADER: reviewer_csrf},
        json={"decision": "APPROVE", "completed_review_modes": []},
    )
    assert approved.status_code == 200
    assert approved.json()["version"]["state"] == "APPROVED"
    return approved.json()["version"], reviewer, reviewer_subject, reviewer_csrf


def test_publication_queue_is_bounded_filtered_and_audit_read_only() -> None:
    app = create_app()
    editor, _, _ = _issue_admin(app, AdminRole.EDITOR)
    reviewer, _, _ = _issue_admin(app, AdminRole.REVIEWER)

    _create_submit_approve(app, title="High publication", content_risk="L2")
    _create_submit_approve(
        app,
        title="Daily publication",
        content_risk="L0",
        domain="DAILY_LIFE",
    )

    forbidden = editor.get("/internal/admin/v1/publication-operations")
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"

    first = reviewer.get(
        "/internal/admin/v1/publication-operations?state=APPROVED&limit=1&offset=0"
    )
    assert first.status_code == 200
    assert len(first.json()["items"]) == 1
    assert first.json()["next_offset"] == 1

    filtered = reviewer.get(
        "/internal/admin/v1/publication-operations"
        "?state=APPROVED&content_risk=L2&primary_domain_code=DAILY_LIFE"
    )
    assert filtered.status_code == 200
    assert [item["title"] for item in filtered.json()["items"]] == [
        "High publication"
    ]

    invalid = reviewer.get("/internal/admin/v1/publication-operations?state=DRAFT")
    assert invalid.status_code == 422


def test_preflight_is_explicit_advisory_and_non_mutating() -> None:
    app = create_app()
    version, reviewer, reviewer_subject, _ = _create_submit_approve(
        app,
        title="Preflight candidate",
    )
    version_id = str(version["id"])
    case_id = str(version["case_id"])

    detail = reviewer.get(f"/internal/admin/v1/publication-operations/{version_id}")
    assert detail.status_code == 200
    assert detail.json()["version"]["state"] == "APPROVED"
    assert detail.json()["approval"]["actor_ref"] == f"admin:{reviewer_subject}"
    assert detail.json()["publication"] is None

    audit_before = reviewer.get(f"/internal/admin/v1/cases/{case_id}/audit").json()[
        "items"
    ]
    preflight = reviewer.get(
        f"/internal/admin/v1/publication-operations/{version_id}/preflight"
    )
    assert preflight.status_code == 200
    assert preflight.json()["eligible"] is True
    assert preflight.json()["advisory_only"] is True
    assert preflight.json()["validation_failures"] == []
    assert preflight.json()["prospective_content_configuration_id"] is not None
    assert preflight.json()["prospective_flow_template_code"] == (
        version["flow_template_code"]
    )

    persisted = app.state.content_authoring_repository.get_version(UUID(version_id))
    assert persisted is not None
    assert persisted.state.value == "APPROVED"
    assert persisted.content_configuration_id is None
    audit_after = reviewer.get(f"/internal/admin/v1/cases/{case_id}/audit").json()[
        "items"
    ]
    assert audit_after == audit_before


def test_preflight_returns_bounded_validation_failures_without_publishing() -> None:
    app = create_app()
    version, reviewer, _, _ = _create_submit_approve(
        app,
        title="Invalid risk candidate",
        content_risk="L9",
    )
    version_id = str(version["id"])

    preflight = reviewer.get(
        f"/internal/admin/v1/publication-operations/{version_id}/preflight"
    )
    assert preflight.status_code == 200
    assert preflight.json()["eligible"] is False
    assert preflight.json()["prospective_content_configuration_id"] is None
    assert [item["code"] for item in preflight.json()["validation_failures"]] == [
        "CONTENT_RISK_UNKNOWN"
    ]


def test_publish_requires_csrf_step_up_ack_and_distinct_approver() -> None:
    app = create_app()
    version, _, _, _ = _create_submit_approve(app, title="Publish candidate")
    version_id = str(version["id"])

    publisher_without_step_up, _, publisher_csrf = _issue_admin(
        app,
        AdminRole.PUBLISHER,
    )
    no_csrf = publisher_without_step_up.post(
        f"/internal/admin/v1/publication-operations/{version_id}/decision",
        json={"decision": "PUBLISH", "acknowledge_immutable": True},
    )
    assert no_csrf.status_code == 403
    assert no_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"

    no_step_up = publisher_without_step_up.post(
        f"/internal/admin/v1/publication-operations/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: publisher_csrf},
        json={"decision": "PUBLISH", "acknowledge_immutable": True},
    )
    assert no_step_up.status_code == 403
    assert no_step_up.json()["code"] == "ADMIN_STEP_UP_REQUIRED"

    publisher, publisher_subject, publisher_csrf = _issue_admin(
        app,
        AdminRole.PUBLISHER,
        step_up=True,
    )
    missing_ack = publisher.post(
        f"/internal/admin/v1/publication-operations/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: publisher_csrf},
        json={"decision": "PUBLISH"},
    )
    assert missing_ack.status_code == 422
    assert missing_ack.json()["code"] == "CONTENT_PUBLICATION_ACK_REQUIRED"

    published = publisher.post(
        f"/internal/admin/v1/publication-operations/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: publisher_csrf},
        json={"decision": "PUBLISH", "acknowledge_immutable": True},
    )
    assert published.status_code == 200
    assert published.json()["version"]["state"] == "PUBLISHED"
    assert published.json()["pin"]["content_configuration_id"] is not None
    assert published.json()["pin"]["flow_template_code"] == (
        version["flow_template_code"]
    )

    persisted = app.state.content_authoring_repository.get_version(UUID(version_id))
    assert persisted is not None
    assert persisted.state.value == "PUBLISHED"
    audit = app.state.content_authoring_repository.list_audit(persisted.case_id)
    assert audit[-1].command == "publish"
    assert audit[-1].actor_ref == f"admin:{publisher_subject}"


def test_same_approver_cannot_publish_even_through_legacy_route() -> None:
    app = create_app()
    version, reviewer_publisher, _, csrf = _create_submit_approve(
        app,
        title="Maker checker candidate",
        approver_roles=(AdminRole.REVIEWER, AdminRole.PUBLISHER),
        approver_step_up=True,
    )
    version_id = str(version["id"])

    bounded = reviewer_publisher.post(
        f"/internal/admin/v1/publication-operations/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"decision": "PUBLISH", "acknowledge_immutable": True},
    )
    assert bounded.status_code == 403
    assert bounded.json()["code"] == "ADMIN_SEPARATION_OF_DUTIES"

    legacy = reviewer_publisher.post(
        f"/internal/admin/v1/case-versions/{version_id}/publish",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert legacy.status_code == 403
    assert legacy.json()["code"] == "ADMIN_SEPARATION_OF_DUTIES"


def test_withdraw_requires_rationale_and_preserves_immutable_version() -> None:
    app = create_app()
    version, _, _, _ = _create_submit_approve(app, title="Withdrawal candidate")
    version_id = str(version["id"])
    publisher, _, csrf = _issue_admin(app, AdminRole.PUBLISHER, step_up=True)

    published = publisher.post(
        f"/internal/admin/v1/publication-operations/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"decision": "PUBLISH", "acknowledge_immutable": True},
    )
    assert published.status_code == 200
    pin = published.json()["pin"]

    missing = publisher.post(
        f"/internal/admin/v1/publication-operations/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"decision": "WITHDRAW", "rationale": ""},
    )
    assert missing.status_code == 422
    assert missing.json()["code"] == "CONTENT_WITHDRAW_RATIONALE_REQUIRED"

    withdrawn = publisher.post(
        f"/internal/admin/v1/publication-operations/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "decision": "WITHDRAW",
            "rationale": "Kaynak güncellemesi bekleniyor.",
        },
    )
    assert withdrawn.status_code == 200
    assert withdrawn.json()["version"]["state"] == "WITHDRAWN"
    assert withdrawn.json()["pin"] == pin

    persisted = app.state.content_authoring_repository.get_version(UUID(version_id))
    assert persisted is not None
    assert persisted.state.value == "WITHDRAWN"
    assert persisted.content_configuration_id is not None
    assert persisted.resolved_flow is not None
    audit = app.state.content_authoring_repository.list_audit(persisted.case_id)
    assert audit[-1].command == "withdraw"
    assert audit[-1].rationale == "Kaynak güncellemesi bekleniyor."
