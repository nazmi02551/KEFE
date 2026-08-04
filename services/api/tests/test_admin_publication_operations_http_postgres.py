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


def _admin_client(
    app,
    subject_id: UUID,
    *,
    step_up: bool = False,
) -> tuple[TestClient, str]:
    now = datetime.now(UTC)
    issued = app.state.admin_session_store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=12),
    )
    if step_up:
        app.state.admin_session_store.record_step_up(issued.session_id, step_up_at=now)
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token


def _create_submit_approve(
    app,
    editor_subject: UUID,
    reviewer_subject: UUID,
) -> dict[str, object]:
    editor, editor_csrf = _admin_client(app, editor_subject)
    reviewer, reviewer_csrf = _admin_client(app, reviewer_subject)
    created = editor.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: editor_csrf},
        json={
            "slug": f"pg-publication-{uuid4().hex[:10]}",
            "content": {
                "title": "Durable publication candidate",
                "summary": "PostgreSQL publication restart proof.",
                "base_format_code": "DILEMMA",
                "primary_domain_code": "DAILY_LIFE",
                "content_risk": "L1",
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
            },
        },
    )
    assert created.status_code == 201
    submitted = editor.post(
        f"/internal/admin/v1/case-versions/{created.json()['id']}/submit",
        headers={ADMIN_CSRF_HEADER: editor_csrf},
    )
    assert submitted.status_code == 200
    approved = reviewer.post(
        f"/internal/admin/v1/content-reviews/{created.json()['id']}/decision",
        headers={ADMIN_CSRF_HEADER: reviewer_csrf},
        json={"decision": "APPROVE", "completed_review_modes": []},
    )
    assert approved.status_code == 200
    return approved.json()["version"]


def test_postgres_publication_operations_survive_publish_withdraw_and_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    editor_subject = _seed_subject(database_url, "EDITOR")
    reviewer_subject = _seed_subject(database_url, "REVIEWER")
    publisher_subject = _seed_subject(database_url, "PUBLISHER")

    try:
        first_app = create_app()
        approved = _create_submit_approve(
            first_app,
            editor_subject,
            reviewer_subject,
        )
        version_id = str(approved["id"])
        case_id = str(approved["case_id"])

        second_app = create_app()
        publisher, publisher_csrf = _admin_client(
            second_app,
            publisher_subject,
            step_up=True,
        )
        queue = publisher.get(
            "/internal/admin/v1/publication-operations"
            "?state=APPROVED&content_risk=L1&primary_domain_code=DAILY_LIFE"
        )
        assert queue.status_code == 200
        assert [item["version_id"] for item in queue.json()["items"]] == [version_id]

        preflight = publisher.get(
            f"/internal/admin/v1/publication-operations/{version_id}/preflight"
        )
        assert preflight.status_code == 200
        assert preflight.json()["eligible"] is True
        prospective_config = preflight.json()["prospective_content_configuration_id"]
        prospective_flow = preflight.json()["prospective_flow_template_code"]

        published = publisher.post(
            f"/internal/admin/v1/publication-operations/{version_id}/decision",
            headers={ADMIN_CSRF_HEADER: publisher_csrf},
            json={"decision": "PUBLISH", "acknowledge_immutable": True},
        )
        assert published.status_code == 200
        assert published.json()["version"]["state"] == "PUBLISHED"
        assert published.json()["pin"]["content_configuration_id"] == prospective_config
        assert published.json()["pin"]["flow_template_code"] == prospective_flow

        third_app = create_app()
        persisted = third_app.state.content_authoring_repository.get_version(UUID(version_id))
        assert persisted is not None
        assert persisted.state.value == "PUBLISHED"
        assert str(persisted.content_configuration_id) == prospective_config
        assert persisted.resolved_flow is not None
        assert persisted.resolved_flow.template_code == prospective_flow

        third_publisher, third_csrf = _admin_client(
            third_app,
            publisher_subject,
            step_up=True,
        )
        published_queue = third_publisher.get(
            "/internal/admin/v1/publication-operations?state=PUBLISHED"
        )
        assert published_queue.status_code == 200
        assert version_id in [
            item["version_id"] for item in published_queue.json()["items"]
        ]

        withdrawn = third_publisher.post(
            f"/internal/admin/v1/publication-operations/{version_id}/decision",
            headers={ADMIN_CSRF_HEADER: third_csrf},
            json={
                "decision": "WITHDRAW",
                "rationale": "Durable withdrawal proof.",
            },
        )
        assert withdrawn.status_code == 200
        assert withdrawn.json()["version"]["state"] == "WITHDRAWN"

        fourth_app = create_app()
        final = fourth_app.state.content_authoring_repository.get_version(UUID(version_id))
        assert final is not None
        assert final.state.value == "WITHDRAWN"
        assert final.content_configuration_id == persisted.content_configuration_id
        assert final.resolved_flow == persisted.resolved_flow

        auditor, _ = _admin_client(fourth_app, reviewer_subject)
        audit = auditor.get(f"/internal/admin/v1/cases/{case_id}/audit")
        assert audit.status_code == 200
        assert [item["command"] for item in audit.json()["items"]] == [
            "create_case",
            "submit_for_review",
            "approve",
            "publish",
            "withdraw",
        ]
        assert audit.json()["items"][-2]["actor_ref"] == f"admin:{publisher_subject}"
        assert audit.json()["items"][-1]["rationale"] == "Durable withdrawal proof."
    finally:
        get_settings.cache_clear()
