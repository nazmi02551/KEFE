from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE


def _issue_admin(app, *roles: AdminRole) -> tuple[TestClient, UUID, str]:
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
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, subject_id, issued.csrf_token


def _create_and_submit(
    editor: TestClient,
    csrf: str,
    *,
    title: str,
    content_risk: str = "L1",
    primary_domain_code: str = "PUBLIC_LIFE",
    required_review_modes: list[str] | None = None,
    completed_review_modes: list[str] | None = None,
) -> dict[str, object]:
    response = editor.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "slug": f"quality-review-{uuid4().hex[:10]}",
            "content": {
                "title": title,
                "summary": "Editorial quality review fixture.",
                "base_format_code": "DILEMMA",
                "primary_domain_code": primary_domain_code,
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
                "required_review_modes": required_review_modes or [],
                "completed_review_modes": completed_review_modes or [],
            },
        },
    )
    assert response.status_code == 201
    version = response.json()
    submitted = editor.post(
        f"/internal/admin/v1/case-versions/{version['id']}/submit",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert submitted.status_code == 200
    assert submitted.json()["state"] == "IN_REVIEW"
    return submitted.json()


def test_review_queue_is_bounded_filtered_and_reviewer_only() -> None:
    app = create_app()
    editor, _, editor_csrf = _issue_admin(app, AdminRole.EDITOR)
    reviewer, _, _ = _issue_admin(app, AdminRole.REVIEWER)

    _create_and_submit(
        editor,
        editor_csrf,
        title="High risk review",
        content_risk="L2",
        primary_domain_code="PUBLIC_LIFE",
    )
    _create_and_submit(
        editor,
        editor_csrf,
        title="Daily review",
        content_risk="L0",
        primary_domain_code="DAILY_LIFE",
    )

    forbidden = editor.get("/internal/admin/v1/content-reviews")
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"

    first = reviewer.get("/internal/admin/v1/content-reviews?limit=1&offset=0")
    assert first.status_code == 200
    assert len(first.json()["items"]) == 1
    assert first.json()["next_offset"] == 1

    second = reviewer.get("/internal/admin/v1/content-reviews?limit=1&offset=1")
    assert second.status_code == 200
    assert len(second.json()["items"]) == 1

    filtered = reviewer.get(
        "/internal/admin/v1/content-reviews?content_risk=L2&primary_domain_code=PUBLIC_LIFE"
    )
    assert filtered.status_code == 200
    assert [item["title"] for item in filtered.json()["items"]] == ["High risk review"]
    assert filtered.json()["items"][0]["required_review_modes"] == []


def test_review_detail_and_decision_enforce_csrf_separation_and_exact_modes() -> None:
    app = create_app()
    submitter, submitter_subject, submitter_csrf = _issue_admin(
        app,
        AdminRole.EDITOR,
        AdminRole.REVIEWER,
    )
    reviewer, reviewer_subject, reviewer_csrf = _issue_admin(app, AdminRole.REVIEWER)

    version = _create_and_submit(
        submitter,
        submitter_csrf,
        title="Attested review",
        required_review_modes=["SOURCE_VERIFY", "LEGAL_REVIEW"],
    )
    version_id = str(version["id"])
    case_id = str(version["case_id"])

    detail = reviewer.get(f"/internal/admin/v1/content-reviews/{version_id}")
    assert detail.status_code == 200
    assert detail.json()["version"]["state"] == "IN_REVIEW"
    assert detail.json()["version"]["required_review_modes"] == [
        "SOURCE_VERIFY",
        "LEGAL_REVIEW",
    ]
    assert detail.json()["submitter_actor_ref"] == f"admin:{submitter_subject}"

    missing_csrf = reviewer.post(
        f"/internal/admin/v1/content-reviews/{version_id}/decision",
        json={
            "decision": "APPROVE",
            "completed_review_modes": ["SOURCE_VERIFY", "LEGAL_REVIEW"],
        },
    )
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"

    self_review = submitter.post(
        f"/internal/admin/v1/content-reviews/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: submitter_csrf},
        json={
            "decision": "APPROVE",
            "completed_review_modes": ["SOURCE_VERIFY", "LEGAL_REVIEW"],
        },
    )
    assert self_review.status_code == 403
    assert self_review.json()["code"] == "ADMIN_SEPARATION_OF_DUTIES"

    legacy_bypass = reviewer.post(
        f"/internal/admin/v1/case-versions/{version_id}/approve",
        headers={ADMIN_CSRF_HEADER: reviewer_csrf},
    )
    assert legacy_bypass.status_code == 422
    assert legacy_bypass.json()["code"] == "CONTENT_REVIEW_ATTESTATION_REQUIRED"

    incomplete = reviewer.post(
        f"/internal/admin/v1/content-reviews/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: reviewer_csrf},
        json={"decision": "APPROVE", "completed_review_modes": ["SOURCE_VERIFY"]},
    )
    assert incomplete.status_code == 422
    assert incomplete.json()["code"] == "CONTENT_REVIEW_MODES_INCOMPLETE"
    assert incomplete.json()["meta"]["missing"] == ["LEGAL_REVIEW"]

    duplicate = reviewer.post(
        f"/internal/admin/v1/content-reviews/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: reviewer_csrf},
        json={
            "decision": "APPROVE",
            "completed_review_modes": ["SOURCE_VERIFY", "SOURCE_VERIFY"],
        },
    )
    assert duplicate.status_code == 422
    assert duplicate.json()["code"] == "CONTENT_REVIEW_MODES_INVALID"

    approved = reviewer.post(
        f"/internal/admin/v1/content-reviews/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: reviewer_csrf},
        json={
            "decision": "APPROVE",
            "completed_review_modes": ["LEGAL_REVIEW", "SOURCE_VERIFY"],
        },
    )
    assert approved.status_code == 200
    assert approved.json()["version"]["state"] == "APPROVED"
    assert approved.json()["version"]["completed_review_modes"] == [
        "SOURCE_VERIFY",
        "LEGAL_REVIEW",
    ]
    assert approved.json()["submitter_actor_ref"] == f"admin:{submitter_subject}"

    audit = reviewer.get(f"/internal/admin/v1/cases/{case_id}/audit")
    assert audit.status_code == 200
    approval = audit.json()["items"][-1]
    assert approval["command"] == "approve"
    assert approval["actor_ref"] == f"admin:{reviewer_subject}"
    assert "SOURCE_VERIFY" in approval["rationale"]
    assert "LEGAL_REVIEW" in approval["rationale"]


def test_reject_requires_rationale_and_clears_stale_attestations() -> None:
    app = create_app()
    editor, _, editor_csrf = _issue_admin(app, AdminRole.EDITOR)
    reviewer, _, reviewer_csrf = _issue_admin(app, AdminRole.REVIEWER)

    version = _create_and_submit(
        editor,
        editor_csrf,
        title="Return to draft",
        required_review_modes=["SOURCE_VERIFY"],
        completed_review_modes=["SOURCE_VERIFY"],
    )
    version_id = str(version["id"])

    missing = reviewer.post(
        f"/internal/admin/v1/content-reviews/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: reviewer_csrf},
        json={"decision": "REJECT", "rationale": ""},
    )
    assert missing.status_code == 422
    assert missing.json()["code"] == "CONTENT_REJECTION_RATIONALE_REQUIRED"

    rejected = reviewer.post(
        f"/internal/admin/v1/content-reviews/{version_id}/decision",
        headers={ADMIN_CSRF_HEADER: reviewer_csrf},
        json={
            "decision": "REJECT",
            "rationale": "Kaynak doğrulaması yeniden yapılmalı.",
            "completed_review_modes": ["SOURCE_VERIFY"],
        },
    )
    assert rejected.status_code == 200
    assert rejected.json()["version"]["state"] == "DRAFT"
    assert rejected.json()["version"]["completed_review_modes"] == []

    persisted = app.state.content_authoring_repository.get_version(UUID(version_id))
    assert persisted is not None
    assert persisted.completed_review_modes == ()
