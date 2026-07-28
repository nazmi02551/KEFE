from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE


def _issue_admin(app, *roles: AdminRole) -> tuple[TestClient, UUID, str, str]:
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

    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, subject_id, issued.session_token, issued.csrf_token


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


def test_configuration_routes_require_admin_capability() -> None:
    app = create_app()
    anonymous = TestClient(app)
    assert anonymous.get("/internal/admin/v1/content-configuration/current").status_code == 401

    editor, _, _, _ = _issue_admin(app, AdminRole.EDITOR)
    forbidden = editor.get("/internal/admin/v1/content-configuration/current")
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"

    manager, _, _, _ = _issue_admin(app, AdminRole.TAXONOMY_MANAGER)
    current = manager.get("/internal/admin/v1/content-configuration/current")
    assert current.status_code == 200
    assert current.json()["state"] == "PUBLISHED"
    assert current.json()["primitives"]
    assert current.json()["capabilities"]
    assert current.json()["flow_templates"]


def test_configuration_mutation_requires_csrf_before_activity_touch() -> None:
    app = create_app()
    manager, _, session_token, csrf_token = _issue_admin(app, AdminRole.TAXONOMY_MANAGER)
    store = app.state.admin_session_store

    before = store.resolve(session_token).principal
    assert before is not None

    missing = manager.post("/internal/admin/v1/content-configuration/drafts")
    assert missing.status_code == 403
    assert missing.json()["code"] == "ADMIN_CSRF_REQUIRED"

    after_missing = store.resolve(session_token).principal
    assert after_missing is not None
    assert after_missing.last_seen_at == before.last_seen_at

    valid = manager.post(
        "/internal/admin/v1/content-configuration/drafts",
        headers={ADMIN_CSRF_HEADER: csrf_token},
    )
    assert valid.status_code == 201
    assert valid.json()["state"] == "DRAFT"

    after_valid = store.resolve(session_token).principal
    assert after_valid is not None
    assert after_valid.last_seen_at >= before.last_seen_at


def test_configuration_lifecycle_uses_server_identity_and_current_step_up_policy() -> None:
    app = create_app()
    manager, subject_id, _, csrf_token = _issue_admin(app, AdminRole.TAXONOMY_MANAGER)

    original = manager.get("/internal/admin/v1/content-configuration/current")
    assert original.status_code == 200
    original_id = original.json()["id"]

    draft = manager.post(
        "/internal/admin/v1/content-configuration/drafts",
        headers={ADMIN_CSRF_HEADER: csrf_token},
    )
    assert draft.status_code == 201
    draft_id = draft.json()["id"]

    payload = _editable_payload(draft.json())
    payload["flow_templates"] = [
        *payload["flow_templates"],
        {
            "code": "ADMIN_HTTP_GENERIC_FLOW",
            "version_no": 1,
            "label_key": "flow.admin_http_generic_flow",
            "entry_step_code": "DECISION",
            "steps": [
                {
                    "code": "DECISION",
                    "primitive_code": "DECISION",
                    "capability_codes": ["COMMIT_FIRST"],
                    "next_step_codes": [],
                    "payload_schema_ref": None,
                }
            ],
            "enabled": True,
        },
    ]

    saved = manager.put(
        f"/internal/admin/v1/content-configuration/versions/{draft_id}",
        headers={ADMIN_CSRF_HEADER: csrf_token},
        json=payload,
    )
    assert saved.status_code == 200
    assert saved.json()["flow_templates"][-1]["code"] == "ADMIN_HTTP_GENERIC_FLOW"

    # TAXONOMY_MANAGE is intentionally not a step-up capability in the current policy.
    published = manager.post(
        f"/internal/admin/v1/content-configuration/versions/{draft_id}/publish",
        headers={ADMIN_CSRF_HEADER: csrf_token},
    )
    assert published.status_code == 200
    assert published.json()["state"] == "PUBLISHED"

    audit = manager.get("/internal/admin/v1/content-configuration/audit")
    assert audit.status_code == 200
    actor_refs = {item["actor_ref"] for item in audit.json()["items"]}
    assert actor_refs == {f"admin:{subject_id}"}

    rollback = manager.post(
        f"/internal/admin/v1/content-configuration/versions/{original_id}/rollback-drafts",
        headers={ADMIN_CSRF_HEADER: csrf_token},
        json={"rationale": "Restore prior known-good composition as a new draft"},
    )
    assert rollback.status_code == 201
    assert rollback.json()["state"] == "DRAFT"
    assert rollback.json()["cloned_from_version_id"] == original_id


def test_configuration_payload_cannot_override_identity_or_lifecycle_metadata() -> None:
    app = create_app()
    manager, _, _, csrf_token = _issue_admin(app, AdminRole.TAXONOMY_MANAGER)

    draft = manager.post(
        "/internal/admin/v1/content-configuration/drafts",
        headers={ADMIN_CSRF_HEADER: csrf_token},
    )
    assert draft.status_code == 201
    draft_id = draft.json()["id"]

    payload = _editable_payload(draft.json())
    payload["actor_ref"] = "admin:attacker-controlled"
    payload["version_no"] = 999
    payload["state"] = "PUBLISHED"

    rejected = manager.put(
        f"/internal/admin/v1/content-configuration/versions/{draft_id}",
        headers={ADMIN_CSRF_HEADER: csrf_token},
        json=payload,
    )
    assert rejected.status_code == 422

    unchanged = manager.get(
        f"/internal/admin/v1/content-configuration/versions/{draft_id}"
    )
    assert unchanged.status_code == 200
    assert unchanged.json()["version_no"] != 999
    assert unchanged.json()["state"] == "DRAFT"
