from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.community_reason.models import (
    CommunityReason,
    CommunityReasonModeration,
    ReasonReportCode,
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


def _seed_reason(
    app,
    *,
    state: CommunityReasonModeration,
    body: str | None,
    created_at: datetime | None = None,
) -> CommunityReason:
    now = created_at or datetime.now(UTC)
    reason = CommunityReason(
        id=uuid4(),
        actor_id=uuid4(),
        session_id=uuid4(),
        case_version_id=uuid4(),
        tags=("FAIRNESS",),
        body=body,
        moderation_state=state,
        created_at=now,
        updated_at=now,
    )
    return app.state.community_reason_repository.create_or_replace(reason)


def _report(app, reason_id: UUID, code: ReasonReportCode, *, created_at: datetime) -> None:
    app.state.community_reason_repository.report(
        report_id=uuid4(),
        reason_id=reason_id,
        reporter_actor_id=uuid4(),
        report_code=code,
        created_at=created_at,
    )


def test_moderation_queues_are_step_up_bounded_and_privacy_safe() -> None:
    app = create_app()
    pending = _seed_reason(
        app,
        state=CommunityReasonModeration.PENDING,
        body="A reason that requires human moderation.",
        created_at=datetime.now(UTC) - timedelta(minutes=10),
    )
    reported = _seed_reason(
        app,
        state=CommunityReasonModeration.NOT_REQUIRED,
        body=None,
        created_at=datetime.now(UTC) - timedelta(minutes=5),
    )
    _report(
        app,
        reported.id,
        ReasonReportCode.PERSONAL_DATA,
        created_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    reviewer_without_step_up, _, _ = _issue_admin(app, AdminRole.REVIEWER)
    denied = reviewer_without_step_up.get(
        "/internal/admin/v1/community-reason-moderation"
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == "ADMIN_STEP_UP_REQUIRED"

    reviewer, _, _ = _issue_admin(app, AdminRole.REVIEWER, step_up=True)
    pending_response = reviewer.get(
        "/internal/admin/v1/community-reason-moderation?kind=PENDING&limit=1"
    )
    assert pending_response.status_code == 200
    assert pending_response.json()["next_offset"] == 1
    pending_item = pending_response.json()["items"][0]
    assert pending_item["reason_id"] == str(pending.id)
    assert pending_item["moderation_state"] == "PENDING"

    reported_response = reviewer.get(
        "/internal/admin/v1/community-reason-moderation"
        "?kind=REPORTED&report_code=PERSONAL_DATA"
    )
    assert reported_response.status_code == 200
    reported_item = reported_response.json()["items"][0]
    assert reported_item["reason_id"] == str(reported.id)
    assert reported_item["report_count"] == 1
    assert reported_item["report_counts_by_code"] == {"PERSONAL_DATA": 1}
    for forbidden in (
        "actor_id",
        "author_actor_id",
        "session_id",
        "weigh_session_id",
        "reporter_actor_id",
        "reporters",
    ):
        assert forbidden not in reported_item


def test_decision_requires_csrf_confirmation_rationale_and_appends_audit() -> None:
    app = create_app()
    reason = _seed_reason(
        app,
        state=CommunityReasonModeration.PENDING,
        body="A pending reason for an explicit decision.",
    )
    reviewer, reviewer_subject, csrf = _issue_admin(
        app,
        AdminRole.REVIEWER,
        step_up=True,
    )
    endpoint = f"/internal/admin/v1/community-reason-moderation/{reason.id}/decision"

    no_csrf = reviewer.post(
        endpoint,
        json={
            "state": "ALLOWED",
            "rationale": "This reason is safe to publish.",
            "confirm_reason_id": str(reason.id),
        },
    )
    assert no_csrf.status_code == 403
    assert no_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"

    wrong_confirmation = reviewer.post(
        endpoint,
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "state": "ALLOWED",
            "rationale": "This reason is safe to publish.",
            "confirm_reason_id": str(uuid4()),
        },
    )
    assert wrong_confirmation.status_code == 422
    assert wrong_confirmation.json()["code"] == (
        "COMMUNITY_REASON_MODERATION_CONFIRMATION_INVALID"
    )

    short_rationale = reviewer.post(
        endpoint,
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "state": "ALLOWED",
            "rationale": "short",
            "confirm_reason_id": str(reason.id),
        },
    )
    assert short_rationale.status_code == 422

    allowed = reviewer.post(
        endpoint,
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "state": "ALLOWED",
            "rationale": "This reason is safe to publish.",
            "confirm_reason_id": str(reason.id),
        },
    )
    assert allowed.status_code == 200
    assert allowed.json()["reason"]["moderation_state"] == "ALLOWED"
    assert allowed.json()["audit"]["actor_ref"] == f"admin:{reviewer_subject}"
    assert allowed.json()["audit"]["previous_state"] == "PENDING"
    assert allowed.json()["audit"]["decided_state"] == "ALLOWED"

    audit = reviewer.get(
        f"/internal/admin/v1/community-reason-moderation/{reason.id}/audit"
    )
    assert audit.status_code == 200
    assert len(audit.json()["items"]) == 1
    assert audit.json()["items"][0]["rationale"] == (
        "This reason is safe to publish."
    )


def test_reported_reason_is_resolved_until_a_new_report_arrives() -> None:
    app = create_app()
    reason = _seed_reason(
        app,
        state=CommunityReasonModeration.NOT_REQUIRED,
        body=None,
    )
    _report(app, reason.id, ReasonReportCode.ABUSE, created_at=datetime.now(UTC))
    reviewer, _, csrf = _issue_admin(app, AdminRole.REVIEWER, step_up=True)

    before = reviewer.get(
        "/internal/admin/v1/community-reason-moderation?kind=REPORTED"
    )
    assert [item["reason_id"] for item in before.json()["items"]] == [str(reason.id)]

    upheld = reviewer.post(
        f"/internal/admin/v1/community-reason-moderation/{reason.id}/decision",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "state": "ALLOWED",
            "rationale": "The report was reviewed and the tags are safe.",
            "confirm_reason_id": str(reason.id),
        },
    )
    assert upheld.status_code == 200

    resolved = reviewer.get(
        "/internal/admin/v1/community-reason-moderation?kind=REPORTED"
    )
    assert resolved.json()["items"] == []

    _report(
        app,
        reason.id,
        ReasonReportCode.MISLEADING,
        created_at=datetime.now(UTC) + timedelta(seconds=1),
    )
    reopened = reviewer.get(
        "/internal/admin/v1/community-reason-moderation?kind=REPORTED"
    )
    assert [item["reason_id"] for item in reopened.json()["items"]] == [str(reason.id)]


def test_blocked_reason_is_terminal_and_legacy_endpoint_cannot_bypass_audit() -> None:
    app = create_app()
    reason = _seed_reason(
        app,
        state=CommunityReasonModeration.PENDING,
        body="A reason blocked through the compatibility endpoint.",
    )
    reviewer, reviewer_subject, csrf = _issue_admin(
        app,
        AdminRole.REVIEWER,
        step_up=True,
    )
    legacy = f"/internal/admin/v1/community-reasons/{reason.id}/moderation"

    missing_rationale = reviewer.post(
        legacy,
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"state": "BLOCKED"},
    )
    assert missing_rationale.status_code == 422
    assert missing_rationale.json()["code"] == (
        "COMMUNITY_REASON_MODERATION_RATIONALE_INVALID"
    )

    blocked = reviewer.post(
        legacy,
        headers={
            ADMIN_CSRF_HEADER: csrf,
            "X-KEFE-Moderation-Rationale": "The text contains disallowed personal data.",
        },
        json={"state": "BLOCKED"},
    )
    assert blocked.status_code == 200
    assert blocked.json()["moderation_state"] == "BLOCKED"

    second = reviewer.post(
        legacy,
        headers={
            ADMIN_CSRF_HEADER: csrf,
            "X-KEFE-Moderation-Rationale": "Attempting to reverse a terminal decision.",
        },
        json={"state": "ALLOWED"},
    )
    assert second.status_code == 409
    assert second.json()["code"] == "COMMUNITY_REASON_MODERATION_STATE_INVALID"

    audit = reviewer.get(
        f"/internal/admin/v1/community-reason-moderation/{reason.id}/audit"
    )
    assert audit.status_code == 200
    assert len(audit.json()["items"]) == 1
    assert audit.json()["items"][0]["actor_ref"] == f"admin:{reviewer_subject}"
