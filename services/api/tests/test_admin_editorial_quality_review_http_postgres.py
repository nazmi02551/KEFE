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


def _admin_client(app, subject_id: UUID) -> tuple[TestClient, str]:
    now = datetime.now(UTC)
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=12),
    )
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token


def _create_and_submit(editor: TestClient, csrf: str) -> dict[str, object]:
    created = editor.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "slug": f"pg-quality-review-{uuid4().hex[:10]}",
            "content": {
                "title": "Durable quality review",
                "summary": "PostgreSQL restart proof.",
                "base_format_code": "DILEMMA",
                "primary_domain_code": "PUBLIC_LIFE",
                "content_risk": "L2",
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
                "required_review_modes": ["SOURCE_VERIFY", "LEGAL_REVIEW"],
            },
        },
    )
    assert created.status_code == 201
    submitted = editor.post(
        f"/internal/admin/v1/case-versions/{created.json()['id']}/submit",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert submitted.status_code == 200
    return submitted.json()


def test_postgres_editorial_quality_review_survives_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    editor_subject = _seed_subject(database_url, "EDITOR")
    reviewer_subject = _seed_subject(database_url, "REVIEWER")

    try:
        first_app = create_app()
        editor, editor_csrf = _admin_client(first_app, editor_subject)
        submitted = _create_and_submit(editor, editor_csrf)
        version_id = str(submitted["id"])
        case_id = str(submitted["case_id"])

        second_app = create_app()
        reviewer, reviewer_csrf = _admin_client(second_app, reviewer_subject)
        queue = reviewer.get(
            "/internal/admin/v1/content-reviews?content_risk=L2&primary_domain_code=PUBLIC_LIFE"
        )
        assert queue.status_code == 200
        assert [item["version_id"] for item in queue.json()["items"]] == [version_id]

        detail = reviewer.get(f"/internal/admin/v1/content-reviews/{version_id}")
        assert detail.status_code == 200
        assert detail.json()["version"]["required_review_modes"] == [
            "SOURCE_VERIFY",
            "LEGAL_REVIEW",
        ]
        assert detail.json()["submitter_actor_ref"] == f"admin:{editor_subject}"

        incomplete = reviewer.post(
            f"/internal/admin/v1/content-reviews/{version_id}/decision",
            headers={ADMIN_CSRF_HEADER: reviewer_csrf},
            json={"decision": "APPROVE", "completed_review_modes": ["SOURCE_VERIFY"]},
        )
        assert incomplete.status_code == 422
        assert incomplete.json()["code"] == "CONTENT_REVIEW_MODES_INCOMPLETE"

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

        third_app = create_app()
        persisted = third_app.state.content_authoring_repository.get_version(UUID(version_id))
        assert persisted is not None
        assert persisted.state.value == "APPROVED"
        assert persisted.completed_review_modes == ("SOURCE_VERIFY", "LEGAL_REVIEW")

        third_reviewer, _ = _admin_client(third_app, reviewer_subject)
        empty_queue = third_reviewer.get("/internal/admin/v1/content-reviews")
        assert empty_queue.status_code == 200
        assert empty_queue.json()["items"] == []

        audit = third_reviewer.get(f"/internal/admin/v1/cases/{case_id}/audit")
        assert audit.status_code == 200
        assert [item["command"] for item in audit.json()["items"]] == [
            "create_case",
            "submit_for_review",
            "approve",
        ]
        assert audit.json()["items"][-1]["actor_ref"] == f"admin:{reviewer_subject}"
    finally:
        get_settings.cache_clear()
