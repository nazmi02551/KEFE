from __future__ import annotations

import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseLocalization,
    MarketScope,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _seed_editor_reviewer(database_url: str) -> UUID:
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
        for role in ("EDITOR", "REVIEWER"):
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


def _create(editor: TestClient, csrf: str) -> dict[str, object]:
    response = editor.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "slug": f"pg-case-builder-{uuid4().hex[:10]}",
            "content": {
                "title": "Durable Case Builder",
                "summary": "Initial durable draft.",
                "base_format_code": "STANDARD_CASE",
                "primary_domain_code": "PUBLIC_LIFE",
                "content_risk": "MEDIUM",
                "issues": [
                    {
                        "code": "primary-issue",
                        "title": "Ana mesele",
                        "questions": [
                            {
                                "stable_code": "primary-question",
                                "prompt": "Ne yapılmalı?",
                                "response_type": "SINGLE_CHOICE",
                                "response_schema": {"options": ["A", "B"]},
                            }
                        ],
                    }
                ],
            },
        },
    )
    assert response.status_code == 201
    return response.json()


def _request_body(version: dict[str, object]) -> dict[str, object]:
    return {
        key: version[key]
        for key in (
            "title",
            "summary",
            "base_format_code",
            "primary_domain_code",
            "content_risk",
            "issues",
            "context_blocks",
            "sources",
            "modifiers",
            "is_fact_bearing",
            "is_real_event",
            "required_review_modes",
            "content_locale",
            "market_scope",
            "country_codes",
            "cultural_context_note",
            "legal_context_note",
            "localizations",
        )
    }


def test_postgres_case_builder_round_trip_survives_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    subject_id = _seed_editor_reviewer(database_url)

    try:
        first_app = create_app()
        editor, csrf = _admin_client(first_app, subject_id)
        created = _create(editor, csrf)
        version_id = UUID(str(created["id"]))
        case_id = str(created["case_id"])

        repository = first_app.state.content_authoring_repository
        current = repository.get_version(version_id)
        assert current is not None
        first_app.state.content_authoring_service.save_draft(
            replace(
                current,
                flow_template_code="STANDARD_WEIGH",
                flow_template_version_no=3,
                content_locale="tr",
                market_scope=MarketScope.COUNTRY_SET,
                country_codes=("TR",),
                cultural_context_note="Kalıcı kültürel bağlam",
                legal_context_note="Kalıcı hukuki bağlam",
                completed_review_modes=("SOURCE_VERIFY",),
                localizations=(
                    AuthoringCaseLocalization(
                        locale="en",
                        title="Durable Case Builder",
                        summary="Durable English summary.",
                    ),
                ),
            )
        )

        second_app = create_app()
        second_editor, second_csrf = _admin_client(second_app, subject_id)
        loaded = second_editor.get(f"/internal/admin/v1/case-builder/case-versions/{version_id}")
        assert loaded.status_code == 200
        loaded_body = loaded.json()
        assert loaded_body["flow_template_code"] == "STANDARD_WEIGH"
        assert loaded_body["flow_template_version_no"] == 3
        assert loaded_body["content_locale"] == "tr"
        assert loaded_body["market_scope"] == "COUNTRY_SET"
        assert loaded_body["localizations"][0]["locale"] == "en"

        update = _request_body(loaded_body)
        update["title"] = "Restart sonrası düzenlenmiş başlık"
        update["summary"] = "Explicit save persisted through PostgreSQL."
        update["country_codes"] = ["TR", "DE"]
        saved = second_editor.put(
            f"/internal/admin/v1/case-builder/case-versions/{version_id}",
            headers={ADMIN_CSRF_HEADER: second_csrf},
            json=update,
        )
        assert saved.status_code == 200
        assert saved.json()["state"] == "DRAFT"
        assert saved.json()["flow_template_version_no"] == 3
        assert saved.json()["completed_review_modes"] == ["SOURCE_VERIFY"]

        third_app = create_app()
        third_editor, third_csrf = _admin_client(third_app, subject_id)
        reloaded = third_editor.get(f"/internal/admin/v1/case-builder/case-versions/{version_id}")
        assert reloaded.status_code == 200
        assert reloaded.json()["title"] == update["title"]
        assert reloaded.json()["country_codes"] == ["TR", "DE"]
        assert reloaded.json()["flow_template_code"] == "STANDARD_WEIGH"

        submitted = third_editor.post(
            f"/internal/admin/v1/case-versions/{version_id}/submit",
            headers={ADMIN_CSRF_HEADER: third_csrf},
        )
        assert submitted.status_code == 200
        assert submitted.json()["state"] == "IN_REVIEW"

        audit = third_editor.get(f"/internal/admin/v1/cases/{case_id}/audit")
        assert audit.status_code == 200
        assert [item["command"] for item in audit.json()["items"]] == [
            "create_case",
            "submit_for_review",
        ]
    finally:
        get_settings.cache_clear()
