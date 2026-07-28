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


def _seed_subject(database_url: str, *roles: str) -> UUID:
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
        for role in roles:
            connection.execute(
                text(
                    """
                    INSERT INTO admin_security.role_assignment (
                        id, subject_id, role, granted_at
                    ) VALUES (
                        :id, :subject_id, :role, :granted_at
                    )
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


def _admin_client(app, subject_id: UUID, *, step_up: bool = False) -> tuple[TestClient, str]:
    now = datetime.now(UTC)
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=12),
    )
    if step_up:
        app.state.admin_session_store.record_step_up(
            issued.session_id,
            step_up_at=now,
        )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token


def _payload() -> dict[str, object]:
    return {
        "slug": f"pg-admin-http-{uuid4().hex[:10]}",
        "content": {
            "title": "PostgreSQL Admin HTTP Case",
            "summary": "Durable secured authoring workflow fixture.",
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


def test_postgres_admin_http_authoring_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()

    editor_id = _seed_subject(database_url, "EDITOR")
    reviewer_id = _seed_subject(database_url, "REVIEWER")
    publisher_id = _seed_subject(database_url, "PUBLISHER")

    try:
        app = create_app()
        editor, editor_csrf = _admin_client(app, editor_id)
        reviewer, reviewer_csrf = _admin_client(app, reviewer_id)
        publisher, publisher_csrf = _admin_client(app, publisher_id, step_up=True)

        created = editor.post(
            "/internal/admin/v1/cases",
            headers={ADMIN_CSRF_HEADER: editor_csrf},
            json=_payload(),
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

        approved = reviewer.post(
            f"/internal/admin/v1/case-versions/{version_id}/approve",
            headers={ADMIN_CSRF_HEADER: reviewer_csrf},
        )
        assert approved.status_code == 200
        assert approved.json()["state"] == "APPROVED"

        published = publisher.post(
            f"/internal/admin/v1/case-versions/{version_id}/publish",
            headers={ADMIN_CSRF_HEADER: publisher_csrf},
        )
        assert published.status_code == 200
        assert published.json()["state"] == "PUBLISHED"

        public_case = editor.get(f"/v1/cases/{case_id}")
        assert public_case.status_code == 200
        assert public_case.json()["case_version_id"] == version_id
        assert public_case.json()["title"] == "PostgreSQL Admin HTTP Case"

        audit = reviewer.get(f"/internal/admin/v1/cases/{case_id}/audit")
        assert audit.status_code == 200
        actor_refs = {entry["actor_ref"] for entry in audit.json()["items"]}
        assert actor_refs == {
            f"admin:{editor_id}",
            f"admin:{reviewer_id}",
            f"admin:{publisher_id}",
        }

        engine = create_engine(database_url)
        with engine.connect() as connection:
            state = connection.execute(
                text(
                    """
                    SELECT lifecycle_state
                    FROM editorial.case_version
                    WHERE id = :version_id
                    """
                ),
                {"version_id": version_id},
            ).scalar_one()
            consumer_state = connection.execute(
                text(
                    """
                    SELECT status
                    FROM content.case_version
                    WHERE id = :version_id
                    """
                ),
                {"version_id": version_id},
            ).scalar_one()
        assert state == "PUBLISHED"
        assert consumer_state == "PUBLISHED"
    finally:
        get_settings.cache_clear()
