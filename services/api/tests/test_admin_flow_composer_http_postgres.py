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


def _durable_flow() -> dict[str, object]:
    return {
        "code": "DURABLE_REVIEW_FLOW",
        "version_no": 1,
        "label_key": "flow.durable_review_flow",
        "entry_step_code": "CONTEXT",
        "steps": [
            {
                "code": "CONTEXT",
                "primitive_code": "CONTEXT",
                "capability_codes": ["COUNTERARGUMENT"],
                "next_step_codes": ["DECISION"],
                "payload_schema_ref": None,
            },
            {
                "code": "DECISION",
                "primitive_code": "DECISION",
                "capability_codes": ["COMMIT_FIRST", "REASON_CAPTURE"],
                "next_step_codes": ["REFLECTION"],
                "payload_schema_ref": None,
            },
            {
                "code": "REFLECTION",
                "primitive_code": "REFLECTION",
                "capability_codes": ["REFLECTION"],
                "next_step_codes": [],
                "payload_schema_ref": None,
            },
        ],
        "enabled": True,
    }


def test_postgres_flow_composer_round_trip_survives_restart(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    subject_id = _seed_taxonomy_manager(database_url)

    try:
        first_app = create_app()
        manager, csrf = _admin_client(first_app, subject_id)
        created = manager.post(
            "/internal/admin/v1/flow-composer/drafts",
            headers={ADMIN_CSRF_HEADER: csrf},
        )
        assert created.status_code == 201
        draft = created.json()
        version_id = UUID(draft["id"])
        primitive_count = len(draft["primitives"])
        capability_count = len(draft["capabilities"])

        saved = manager.put(
            f"/internal/admin/v1/flow-composer/configuration-versions/{version_id}",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={"flow_templates": [*draft["flow_templates"], _durable_flow()]},
        )
        assert saved.status_code == 200
        assert saved.json()["state"] == "DRAFT"
        assert saved.json()["flow_templates"][-1]["code"] == "DURABLE_REVIEW_FLOW"

        second_app = create_app()
        second_manager, second_csrf = _admin_client(second_app, subject_id)
        loaded = second_manager.get(
            f"/internal/admin/v1/flow-composer/configuration-versions/{version_id}"
        )
        assert loaded.status_code == 200
        loaded_body = loaded.json()
        assert loaded_body["state"] == "DRAFT"
        assert len(loaded_body["primitives"]) == primitive_count
        assert len(loaded_body["capabilities"]) == capability_count
        assert loaded_body["flow_templates"][-1]["code"] == "DURABLE_REVIEW_FLOW"
        assert loaded_body["flow_templates"][-1]["steps"][1]["next_step_codes"] == [
            "REFLECTION"
        ]

        updated_flows = loaded_body["flow_templates"]
        updated_flows[-1]["label_key"] = "flow.durable_review_flow.updated"
        resaved = second_manager.put(
            f"/internal/admin/v1/flow-composer/configuration-versions/{version_id}",
            headers={ADMIN_CSRF_HEADER: second_csrf},
            json={"flow_templates": updated_flows},
        )
        assert resaved.status_code == 200

        third_app = create_app()
        third_manager, _ = _admin_client(third_app, subject_id)
        reloaded = third_manager.get(
            f"/internal/admin/v1/flow-composer/configuration-versions/{version_id}"
        )
        assert reloaded.status_code == 200
        assert reloaded.json()["flow_templates"][-1]["label_key"] == (
            "flow.durable_review_flow.updated"
        )

        audit = third_manager.get(
            f"/internal/admin/v1/flow-composer/configuration-versions/{version_id}/audit"
        )
        assert audit.status_code == 200
        assert [item["command"] for item in audit.json()["items"]] == [
            "CREATE_DRAFT_FROM_CURRENT",
            "SAVE_DRAFT",
            "SAVE_DRAFT",
        ]
    finally:
        get_settings.cache_clear()
