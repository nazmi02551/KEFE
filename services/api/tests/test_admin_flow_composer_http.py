from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE


def _issue_admin(app, *roles: AdminRole) -> tuple[TestClient, str]:
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
    return client, issued.csrf_token


def _valid_added_flow() -> dict[str, object]:
    return {
        "code": "EDITORIAL_LINEAR",
        "version_no": 1,
        "label_key": "flow.editorial_linear",
        "entry_step_code": "CONTEXT",
        "steps": [
            {
                "code": "CONTEXT",
                "primitive_code": "CONTEXT",
                "capability_codes": ["SOURCE_REVEAL"],
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
    }


def test_flow_composer_requires_taxonomy_capability_and_same_session_csrf() -> None:
    app = create_app()
    editor, _ = _issue_admin(app, AdminRole.EDITOR)
    manager, csrf = _issue_admin(app, AdminRole.TAXONOMY_MANAGER)

    forbidden = editor.get(
        "/internal/admin/v1/flow-composer/configuration-versions/"
        "77777777-7777-4777-8777-777777777777"
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"

    missing_csrf = manager.post("/internal/admin/v1/flow-composer/drafts")
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"

    created = manager.post(
        "/internal/admin/v1/flow-composer/drafts",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["state"] == "DRAFT"
    assert body["cloned_from_version_id"] == "77777777-7777-4777-8777-777777777777"
    assert body["primitives"]
    assert body["capabilities"]
    assert body["flow_templates"]


def test_flow_composer_replaces_only_flow_templates_and_keeps_draft() -> None:
    app = create_app()
    manager, csrf = _issue_admin(app, AdminRole.TAXONOMY_MANAGER)
    created = manager.post(
        "/internal/admin/v1/flow-composer/drafts",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert created.status_code == 201
    draft = created.json()
    version_id = UUID(draft["id"])
    before = app.state.content_configuration_repository.get(version_id)
    assert before is not None

    flow_templates = [*draft["flow_templates"], _valid_added_flow()]
    missing_csrf = manager.put(
        f"/internal/admin/v1/flow-composer/configuration-versions/{version_id}",
        json={"flow_templates": flow_templates},
    )
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"

    saved = manager.put(
        f"/internal/admin/v1/flow-composer/configuration-versions/{version_id}",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"flow_templates": flow_templates},
    )
    assert saved.status_code == 200
    assert saved.json()["state"] == "DRAFT"
    assert saved.json()["flow_templates"][-1]["code"] == "EDITORIAL_LINEAR"

    after = app.state.content_configuration_repository.get(version_id)
    assert after is not None
    assert after.flow_templates[-1].code == "EDITORIAL_LINEAR"
    for field in (
        "domains",
        "topics",
        "base_formats",
        "modifiers",
        "modifier_compatibility",
        "primitives",
        "capabilities",
        "risks",
        "claim_states",
        "source_kinds",
        "disclosure_levels",
        "created_by",
        "created_at",
        "cloned_from_version_id",
    ):
        assert getattr(after, field) == getattr(before, field)

    audit = manager.get(
        f"/internal/admin/v1/flow-composer/configuration-versions/{version_id}/audit"
    )
    assert audit.status_code == 200
    assert [item["command"] for item in audit.json()["items"]] == [
        "CREATE_DRAFT_FROM_CURRENT",
        "SAVE_DRAFT",
    ]


def test_flow_composer_rejects_unreachable_and_cyclic_graphs() -> None:
    app = create_app()
    manager, csrf = _issue_admin(app, AdminRole.TAXONOMY_MANAGER)
    created = manager.post(
        "/internal/admin/v1/flow-composer/drafts",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert created.status_code == 201
    version_id = created.json()["id"]

    unreachable = {
        "code": "UNREACHABLE",
        "version_no": 1,
        "label_key": "flow.unreachable",
        "entry_step_code": "A",
        "steps": [
            {
                "code": "A",
                "primitive_code": "CONTEXT",
                "capability_codes": [],
                "next_step_codes": ["B"],
                "payload_schema_ref": None,
            },
            {
                "code": "B",
                "primitive_code": "DECISION",
                "capability_codes": [],
                "next_step_codes": [],
                "payload_schema_ref": None,
            },
            {
                "code": "C",
                "primitive_code": "REFLECTION",
                "capability_codes": [],
                "next_step_codes": [],
                "payload_schema_ref": None,
            },
        ],
        "enabled": True,
    }
    response = manager.put(
        f"/internal/admin/v1/flow-composer/configuration-versions/{version_id}",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"flow_templates": [unreachable]},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "CONTENT_CONFIG_FLOW_UNREACHABLE"
    assert response.json()["meta"]["step_codes"] == ["C"]

    cyclic = {
        "code": "CYCLIC",
        "version_no": 1,
        "label_key": "flow.cyclic",
        "entry_step_code": "A",
        "steps": [
            {
                "code": "A",
                "primitive_code": "CONTEXT",
                "capability_codes": [],
                "next_step_codes": ["B", "C"],
                "payload_schema_ref": None,
            },
            {
                "code": "B",
                "primitive_code": "DECISION",
                "capability_codes": [],
                "next_step_codes": ["A"],
                "payload_schema_ref": None,
            },
            {
                "code": "C",
                "primitive_code": "REFLECTION",
                "capability_codes": [],
                "next_step_codes": [],
                "payload_schema_ref": None,
            },
        ],
        "enabled": True,
    }
    response = manager.put(
        f"/internal/admin/v1/flow-composer/configuration-versions/{version_id}",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"flow_templates": [cyclic]},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "CONTENT_CONFIG_FLOW_CYCLIC"


def test_flow_composer_cannot_publish_or_mutate_published_configuration() -> None:
    app = create_app()
    manager, csrf = _issue_admin(app, AdminRole.TAXONOMY_MANAGER)
    current_id = "77777777-7777-4777-8777-777777777777"
    current = manager.get(
        f"/internal/admin/v1/flow-composer/configuration-versions/{current_id}"
    )
    assert current.status_code == 200
    assert current.json()["state"] == "PUBLISHED"

    immutable = manager.put(
        f"/internal/admin/v1/flow-composer/configuration-versions/{current_id}",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={"flow_templates": current.json()["flow_templates"]},
    )
    assert immutable.status_code == 409
    assert immutable.json()["code"] == "CONTENT_CONFIG_IMMUTABLE"

    no_publish_route = manager.post(
        f"/internal/admin/v1/flow-composer/configuration-versions/{current_id}/publish",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert no_publish_route.status_code == 404
