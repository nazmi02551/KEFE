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


def _seed_taxonomy_manager(database_url: str) -> UUID:
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
                    :id, :subject_id, 'TAXONOMY_MANAGER', :granted_at
                )
                """
            ),
            {
                "id": uuid4(),
                "subject_id": subject_id,
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


def _editable_payload(body: dict[str, object]) -> dict[str, object]:
    fields = {
        "domains",
        "topics",
        "base_formats",
        "modifiers",
        "modifier_compatibility",
        "primitives",
        "capabilities",
        "flow_templates",
        "risks",
        "claim_states",
        "source_kinds",
        "disclosure_levels",
    }
    return {key: body[key] for key in fields}


def test_postgres_admin_content_configuration_http_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()

    manager_id = _seed_taxonomy_manager(database_url)

    try:
        app = create_app()
        manager, csrf = _admin_client(app, manager_id)

        current = manager.get("/internal/admin/v1/content-configuration/current")
        assert current.status_code == 200
        current_id = current.json()["id"]

        draft = manager.post(
            "/internal/admin/v1/content-configuration/drafts",
            headers={ADMIN_CSRF_HEADER: csrf},
        )
        assert draft.status_code == 201
        draft_id = draft.json()["id"]

        payload = _editable_payload(draft.json())
        payload["flow_templates"] = [
            *payload["flow_templates"],
            {
                "code": "PG_ADMIN_HTTP_GENERIC_FLOW",
                "version_no": 1,
                "label_key": "flow.pg_admin_http_generic_flow",
                "entry_step_code": "CONTEXT",
                "steps": [
                    {
                        "code": "CONTEXT",
                        "primitive_code": "CONTEXT",
                        "capability_codes": ["PROCESS_ANALYSIS"],
                        "next_step_codes": ["DECISION"],
                        "payload_schema_ref": None,
                    },
                    {
                        "code": "DECISION",
                        "primitive_code": "DECISION",
                        "capability_codes": ["COMMIT_FIRST"],
                        "next_step_codes": [],
                        "payload_schema_ref": None,
                    },
                ],
                "enabled": True,
            },
        ]

        saved = manager.put(
            f"/internal/admin/v1/content-configuration/versions/{draft_id}",
            headers={ADMIN_CSRF_HEADER: csrf},
            json=payload,
        )
        assert saved.status_code == 200
        assert saved.json()["flow_templates"][-1]["code"] == "PG_ADMIN_HTTP_GENERIC_FLOW"

        published = manager.post(
            f"/internal/admin/v1/content-configuration/versions/{draft_id}/publish",
            headers={ADMIN_CSRF_HEADER: csrf},
        )
        assert published.status_code == 200
        assert published.json()["state"] == "PUBLISHED"

        reread = manager.get(
            f"/internal/admin/v1/content-configuration/versions/{draft_id}"
        )
        assert reread.status_code == 200
        assert reread.json()["flow_templates"][-1]["code"] == "PG_ADMIN_HTTP_GENERIC_FLOW"

        audit = manager.get("/internal/admin/v1/content-configuration/audit")
        assert audit.status_code == 200
        relevant = [
            entry
            for entry in audit.json()["items"]
            if entry["config_version_id"] == draft_id
        ]
        assert [entry["command"] for entry in relevant] == [
            "CREATE_DRAFT_FROM_CURRENT",
            "SAVE_DRAFT",
            "PUBLISH",
        ]
        assert {entry["actor_ref"] for entry in relevant} == {f"admin:{manager_id}"}

        rollback = manager.post(
            f"/internal/admin/v1/content-configuration/versions/{current_id}/rollback-drafts",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={"rationale": "Create a recoverable historical configuration draft"},
        )
        assert rollback.status_code == 201
        assert rollback.json()["state"] == "DRAFT"
        assert rollback.json()["cloned_from_version_id"] == current_id

        engine = create_engine(database_url)
        with engine.connect() as connection:
            published_count = connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM content_config.configuration_version
                    WHERE lifecycle_state = 'PUBLISHED'
                    """
                )
            ).scalar_one()
            stored = connection.execute(
                text(
                    """
                    SELECT aggregate
                    FROM content_config.configuration_version
                    WHERE id = :version_id
                    """
                ),
                {"version_id": draft_id},
            ).scalar_one()

        assert published_count == 1
        assert stored["flow_templates"][-1]["code"] == "PG_ADMIN_HTTP_GENERIC_FLOW"
    finally:
        get_settings.cache_clear()
