from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _seed_subject(database_url: str, role: str) -> UUID:
    subject_id = uuid4()
    now = datetime.now(UTC)
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
                "granted_at": now,
            },
        )
    return subject_id


def _admin_client(app, subject_id: UUID) -> tuple[TestClient, str]:
    now = datetime.now(UTC)
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=12),
    )
    app.state.admin_session_store.record_step_up(issued.session_id, step_up_at=now)
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token


def _seed_reason(database_url: str) -> tuple[UUID, UUID, UUID]:
    engine = create_engine(database_url)
    author_id = uuid4()
    reporter_id = uuid4()
    case_id = uuid4()
    version_id = uuid4()
    session_id = uuid4()
    reason_id = uuid4()
    now = datetime.now(UTC) - timedelta(minutes=5)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO identity.actor (id, actor_kind, state, created_at)
                VALUES
                    (:author_id, 'GUEST', 'ACTIVE', :now),
                    (:reporter_id, 'GUEST', 'ACTIVE', :now)
                """
            ),
            {"author_id": author_id, "reporter_id": reporter_id, "now": now},
        )
        connection.execute(
            text(
                """
                INSERT INTO content.case_item (
                    id, slug, base_format_code, primary_domain_code,
                    lifecycle_state, content_risk, created_at, updated_at
                ) VALUES (
                    :id, :slug, 'DILEMMA', 'DAILY_LIFE',
                    'PUBLISHED', 'L0', :now, :now
                )
                """
            ),
            {"id": case_id, "slug": f"reason-moderation-{case_id.hex}", "now": now},
        )
        connection.execute(
            text(
                """
                INSERT INTO content.case_version (
                    id, case_id, version_no, status, title, summary,
                    base_format_code, primary_domain_code, content_risk,
                    accepts_weighs, published_at, created_at
                ) VALUES (
                    :id, :case_id, 1, 'PUBLISHED', 'Moderation case',
                    'Durable moderation fixture', 'DILEMMA', 'DAILY_LIFE', 'L0',
                    true, :now, :now
                )
                """
            ),
            {"id": version_id, "case_id": case_id, "now": now},
        )
        connection.execute(
            text(
                """
                INSERT INTO decision.weigh_session (
                    id, actor_id, case_id, case_version_id, state,
                    commit_idempotency_key, started_at, committed_at,
                    created_at, updated_at
                ) VALUES (
                    :id, :actor_id, :case_id, :case_version_id, 'COMMITTED',
                    :commit_key, :now, :now, :now, :now
                )
                """
            ),
            {
                "id": session_id,
                "actor_id": author_id,
                "case_id": case_id,
                "case_version_id": version_id,
                "commit_key": f"reason-{session_id}",
                "now": now,
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO community.reason (
                    id, actor_id, session_id, case_version_id, tags, body,
                    moderation_state, created_at, updated_at
                ) VALUES (
                    :id, :actor_id, :session_id, :case_version_id,
                    '["FAIRNESS"]'::jsonb,
                    'A durable reason requiring moderation.',
                    'PENDING', :now, :now
                )
                """
            ),
            {
                "id": reason_id,
                "actor_id": author_id,
                "session_id": session_id,
                "case_version_id": version_id,
                "now": now,
            },
        )
    return reason_id, version_id, reporter_id


def _insert_report(
    database_url: str,
    *,
    reason_id: UUID,
    reporter_id: UUID,
    report_code: str,
) -> None:
    engine = create_engine(database_url)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO community.reason_report (
                    id, reason_id, reporter_actor_id, report_code, created_at
                ) VALUES (:id, :reason_id, :reporter_id, :report_code, :created_at)
                """
            ),
            {
                "id": uuid4(),
                "reason_id": reason_id,
                "reporter_id": reporter_id,
                "report_code": report_code,
                "created_at": datetime.now(UTC) + timedelta(seconds=1),
            },
        )


def test_postgres_reason_moderation_survives_decisions_reports_and_restarts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    reviewer_subject = _seed_subject(database_url, "REVIEWER")
    reason_id, case_version_id, reporter_id = _seed_reason(database_url)

    try:
        first_app = create_app()
        reviewer, csrf = _admin_client(first_app, reviewer_subject)
        pending = reviewer.get(
            "/internal/admin/v1/community-reason-moderation"
            f"?kind=PENDING&case_version_id={case_version_id}"
        )
        assert pending.status_code == 200
        assert [item["reason_id"] for item in pending.json()["items"]] == [
            str(reason_id)
        ]
        assert "actor_id" not in pending.json()["items"][0]

        allowed = reviewer.post(
            f"/internal/admin/v1/community-reason-moderation/{reason_id}/decision",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={
                "state": "ALLOWED",
                "rationale": "The text is safe after a complete human review.",
                "confirm_reason_id": str(reason_id),
            },
        )
        assert allowed.status_code == 200
        first_audit_id = allowed.json()["audit"]["audit_id"]

        second_app = create_app()
        second_reviewer, _ = _admin_client(second_app, reviewer_subject)
        audit = second_reviewer.get(
            f"/internal/admin/v1/community-reason-moderation/{reason_id}/audit"
        )
        assert audit.status_code == 200
        assert audit.json()["items"][0]["audit_id"] == first_audit_id
        assert audit.json()["items"][0]["actor_ref"] == f"admin:{reviewer_subject}"

        _insert_report(
            database_url,
            reason_id=reason_id,
            reporter_id=reporter_id,
            report_code="PERSONAL_DATA",
        )

        third_app = create_app()
        third_reviewer, third_csrf = _admin_client(third_app, reviewer_subject)
        reported = third_reviewer.get(
            "/internal/admin/v1/community-reason-moderation"
            f"?kind=REPORTED&case_version_id={case_version_id}"
            "&report_code=PERSONAL_DATA"
        )
        assert reported.status_code == 200
        assert reported.json()["items"][0]["report_counts_by_code"] == {
            "PERSONAL_DATA": 1
        }
        assert "reporter_actor_id" not in reported.json()["items"][0]

        blocked = third_reviewer.post(
            f"/internal/admin/v1/community-reason-moderation/{reason_id}/decision",
            headers={ADMIN_CSRF_HEADER: third_csrf},
            json={
                "state": "BLOCKED",
                "rationale": "The new report confirms personal data exposure.",
                "confirm_reason_id": str(reason_id),
            },
        )
        assert blocked.status_code == 200
        assert blocked.json()["reason"]["moderation_state"] == "BLOCKED"

        fourth_app = create_app()
        final_reason = fourth_app.state.community_reason_repository.get(reason_id)
        assert final_reason is not None
        assert final_reason.moderation_state.value == "BLOCKED"
        final_audit = fourth_app.state.community_reason_repository.moderation_audit(
            reason_id=reason_id,
            limit=100,
        )
        assert [entry.decided_state.value for entry in final_audit] == [
            "BLOCKED",
            "ALLOWED",
        ]
        assert final_audit[0].rationale == (
            "The new report confirms personal data exposure."
        )
    finally:
        get_settings.cache_clear()
