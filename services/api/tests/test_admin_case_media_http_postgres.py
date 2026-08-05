from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.case_media.service import CaseMediaService


class _AllowAllDeliveryGate:
    def permits(self, delivery_ref: str) -> bool:
        return delivery_ref.startswith("media-ref:")


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
            text("INSERT INTO admin_security.subject (id, state) VALUES (:id, 'ACTIVE')"),
            {"id": subject_id},
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


def _admin_client(app, subject_id: UUID, *, step_up: bool) -> tuple[TestClient, str]:
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


def _create_case_version(client: TestClient, csrf: str) -> UUID:
    response = client.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "slug": f"postgres-media-{uuid4().hex[:10]}",
            "content": {
                "title": "PostgreSQL media Case",
                "summary": "Restart-safe Case media fixture.",
                "base_format_code": "CHALLENGE_CARD",
                "primary_domain_code": "CIVIC",
                "content_risk": "L0",
                "issues": [],
                "context_blocks": [],
                "sources": [],
                "modifiers": [],
                "is_fact_bearing": False,
                "is_real_event": False,
                "required_review_modes": [],
                "completed_review_modes": [],
            },
        },
    )
    assert response.status_code == 201, response.text
    return UUID(response.json()["id"])


def _registration() -> dict[str, object]:
    return {
        "asset_key": "postgres-case-hero",
        "kind": "IMAGE",
        "delivery_ref": "media-ref:catalog/postgres-case-hero/v1",
        "content_hash": "b" * 64,
        "byte_length": 4096,
        "media_type": "image/avif",
        "title": "PostgreSQL Case hero",
        "alt_text": "Abstract balance scale used as presentation-only Case media.",
        "caption": "Restart continuity fixture.",
        "credit_label": "KEFE Editorial",
        "source_label": "Internal licensed media catalog",
        "poster_asset_key": None,
    }


def test_postgres_case_media_restart_projection_and_immutability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    editor_subject = _seed_subject(database_url, "EDITOR")
    reviewer_subject = _seed_subject(database_url, "REVIEWER")

    try:
        first_app = create_app()
        editor, csrf = _admin_client(first_app, editor_subject, step_up=True)
        version_id = _create_case_version(editor, csrf)
        created = editor.post(
            "/internal/admin/v1/case-media",
            headers={ADMIN_CSRF_HEADER: csrf},
            json=_registration(),
        )
        assert created.status_code == 201, created.text
        asset_id = UUID(created.json()["asset"]["media_asset_id"])

        assert (
            editor.post(
                f"/internal/admin/v1/case-media/{asset_id}/ready",
                headers={ADMIN_CSRF_HEADER: csrf},
            ).status_code
            == 200
        )
        bound = editor.post(
            f"/internal/admin/v1/case-media/{asset_id}/bindings",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={
                "case_version_id": str(version_id),
                "slot": "HERO",
                "priority": 900,
                "autoplay": False,
                "muted": False,
                "looping": False,
            },
        )
        assert bound.status_code == 200, bound.text
        binding_id = UUID(bound.json()["binding"]["binding_id"])

        second_app = create_app()
        second_editor, second_csrf = _admin_client(
            second_app,
            editor_subject,
            step_up=True,
        )
        projection = second_editor.get(
            f"/internal/admin/v1/case-media/case-versions/{version_id}/projection"
        )
        assert projection.status_code == 200
        assert projection.json()["preview_fallback"] is False
        assert projection.json()["items"] == []

        eligible = CaseMediaService(
            repository=second_app.state.case_media_repository,
            authoring=second_app.state.content_authoring_repository,
            delivery_gate=_AllowAllDeliveryGate(),
        ).project(version_id)
        assert [item.asset_key for item in eligible] == ["postgres-case-hero"]

        reviewer, _ = _admin_client(second_app, reviewer_subject, step_up=False)
        audit = reviewer.get(f"/internal/admin/v1/case-media/{asset_id}/audit")
        assert audit.status_code == 200
        assert [item["command"] for item in audit.json()["items"]] == [
            "REGISTER",
            "MARK_READY",
        ]
        audit_id = UUID(audit.json()["items"][0]["audit_id"])

        engine = create_engine(database_url)
        with pytest.raises(DBAPIError), engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO media.case_version_binding (
                        binding_id, case_version_id, media_asset_id, slot, priority,
                        autoplay, muted, looping, bound_by, bound_at
                    ) VALUES (
                        :binding_id, :case_version_id, :media_asset_id, 'CONTEXT', 800,
                        false, true, false, 'test:direct', now()
                    )
                    """
                ),
                {
                    "binding_id": uuid4(),
                    "case_version_id": version_id,
                    "media_asset_id": asset_id,
                },
            )
        with pytest.raises(DBAPIError), engine.begin() as connection:
            connection.execute(
                text("UPDATE media.asset SET title = 'mutated' WHERE media_asset_id = :id"),
                {"id": asset_id},
            )
        with pytest.raises(DBAPIError), engine.begin() as connection:
            connection.execute(
                text("UPDATE media.asset_audit SET actor_ref = 'mutated' WHERE audit_id = :id"),
                {"id": audit_id},
            )
        with pytest.raises(DBAPIError), engine.begin() as connection:
            connection.execute(
                text("UPDATE media.case_version_binding SET priority = 1 WHERE binding_id = :id"),
                {"id": binding_id},
            )

        retired = second_editor.post(
            f"/internal/admin/v1/case-media/{asset_id}/retire",
            headers={ADMIN_CSRF_HEADER: second_csrf},
        )
        assert retired.status_code == 200
        with pytest.raises(DBAPIError), engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO media.case_version_binding (
                        binding_id, case_version_id, media_asset_id, slot, priority,
                        autoplay, muted, looping, bound_by, bound_at
                    ) VALUES (
                        :binding_id, :case_version_id, :media_asset_id, 'REVEAL', 700,
                        false, false, false, 'test:direct', now()
                    )
                    """
                ),
                {
                    "binding_id": uuid4(),
                    "case_version_id": version_id,
                    "media_asset_id": asset_id,
                },
            )
        with pytest.raises(DBAPIError), engine.begin() as connection:
            connection.execute(
                text("UPDATE media.asset SET state = 'READY' WHERE media_asset_id = :id"),
                {"id": asset_id},
            )
        with pytest.raises(DBAPIError), engine.begin() as connection:
            connection.execute(
                text("DELETE FROM media.asset WHERE media_asset_id = :id"),
                {"id": asset_id},
            )

        third_app = create_app()
        third_editor, _ = _admin_client(third_app, editor_subject, step_up=True)
        after = third_editor.get(
            f"/internal/admin/v1/case-media/case-versions/{version_id}/projection"
        )
        assert after.status_code == 200
        assert after.json()["items"] == []
        third_reviewer, _ = _admin_client(third_app, reviewer_subject, step_up=False)
        final_audit = third_reviewer.get(f"/internal/admin/v1/case-media/{asset_id}/audit")
        assert final_audit.status_code == 200
        assert [item["command"] for item in final_audit.json()["items"]] == [
            "REGISTER",
            "MARK_READY",
            "RETIRE",
        ]
    finally:
        get_settings.cache_clear()
