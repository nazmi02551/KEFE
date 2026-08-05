from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.case_media.service import CaseMediaService


class _AllowAllDeliveryGate:
    def permits(self, delivery_ref: str) -> bool:
        return delivery_ref.startswith("media-ref:")


def _admin(app, role: AdminRole, *, step_up: bool) -> tuple[TestClient, str]:
    store = app.state.admin_session_store
    assert isinstance(store, InMemoryAdminSessionStore)
    subject = uuid4()
    store.upsert_subject(subject, roles=frozenset({role}))
    now = datetime.now(UTC)
    issued = store.issue(
        admin_subject_id=subject,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=12),
    )
    if step_up:
        store.record_step_up(issued.session_id, step_up_at=now)
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued.csrf_token


def _case_version(client: TestClient, csrf: str) -> UUID:
    response = client.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "slug": f"media-case-{uuid4().hex[:8]}",
            "content": {
                "title": "Case with media",
                "summary": "A bounded Case used to verify media binding.",
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
        "asset_key": "case-hero-one",
        "kind": "IMAGE",
        "delivery_ref": "media-ref:catalog/case-hero-one/v1",
        "content_hash": "a" * 64,
        "byte_length": 2048,
        "media_type": "image/webp",
        "title": "Case hero",
        "alt_text": "Abstract scales representing a balanced decision.",
        "caption": "Presentation-only Case media.",
        "credit_label": "KEFE Editorial",
        "source_label": "Internal licensed media catalog",
        "poster_asset_key": None,
    }


def test_media_requires_step_up_and_preserves_preview_isolation() -> None:
    app = create_app()
    editor, csrf = _admin(app, AdminRole.EDITOR, step_up=False)
    denied = editor.post(
        "/internal/admin/v1/case-media",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_registration(),
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == "ADMIN_STEP_UP_REQUIRED"

    editor, csrf = _admin(app, AdminRole.EDITOR, step_up=True)
    created = editor.post(
        "/internal/admin/v1/case-media",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_registration(),
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["asset"]["state"] == "REGISTERED"
    assert body["replayed"] is False
    assert "assets/media" not in str(body)
    asset_id = UUID(body["asset"]["media_asset_id"])

    replay = editor.post(
        "/internal/admin/v1/case-media",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_registration(),
    )
    assert replay.status_code == 201
    assert replay.json()["replayed"] is True
    assert UUID(replay.json()["asset"]["media_asset_id"]) == asset_id


def test_ready_binding_projection_and_retirement_are_explicit() -> None:
    app = create_app()
    editor, csrf = _admin(app, AdminRole.EDITOR, step_up=True)
    version_id = _case_version(editor, csrf)
    created = editor.post(
        "/internal/admin/v1/case-media",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_registration(),
    )
    asset_id = UUID(created.json()["asset"]["media_asset_id"])

    before_ready = editor.post(
        f"/internal/admin/v1/case-media/{asset_id}/bindings",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "case_version_id": str(version_id),
            "slot": "HERO",
            "priority": 100,
            "autoplay": False,
            "muted": False,
            "looping": False,
        },
    )
    assert before_ready.status_code == 409
    assert before_ready.json()["code"] == "CASE_MEDIA_STATE_INVALID"

    ready = editor.post(
        f"/internal/admin/v1/case-media/{asset_id}/ready",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert ready.status_code == 200
    assert ready.json()["asset"]["state"] == "READY"

    bound = editor.post(
        f"/internal/admin/v1/case-media/{asset_id}/bindings",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "case_version_id": str(version_id),
            "slot": "HERO",
            "priority": 100,
            "autoplay": False,
            "muted": False,
            "looping": False,
        },
    )
    assert bound.status_code == 200, bound.text

    projected = editor.get(f"/internal/admin/v1/case-media/case-versions/{version_id}/projection")
    assert projected.status_code == 200
    assert projected.json()["preview_fallback"] is False
    assert projected.json()["items"] == []

    eligible = CaseMediaService(
        repository=app.state.case_media_repository,
        authoring=app.state.content_authoring_repository,
        delivery_gate=_AllowAllDeliveryGate(),
    ).project(version_id)
    assert [item.asset_key for item in eligible] == ["case-hero-one"]

    retired = editor.post(
        f"/internal/admin/v1/case-media/{asset_id}/retire",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert retired.status_code == 200
    assert retired.json()["asset"]["state"] == "RETIRED"
    after = editor.get(f"/internal/admin/v1/case-media/case-versions/{version_id}/projection")
    assert after.status_code == 200
    assert after.json()["items"] == []

    reviewer, _ = _admin(app, AdminRole.REVIEWER, step_up=False)
    audit = reviewer.get(f"/internal/admin/v1/case-media/{asset_id}/audit")
    assert audit.status_code == 200
    assert [item["command"] for item in audit.json()["items"]] == [
        "REGISTER",
        "MARK_READY",
        "RETIRE",
    ]
