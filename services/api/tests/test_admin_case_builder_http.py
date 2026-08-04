from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseLocalization,
    MarketScope,
)


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


def _create_case(editor: TestClient, csrf: str) -> dict[str, object]:
    response = editor.post(
        "/internal/admin/v1/cases",
        headers={ADMIN_CSRF_HEADER: csrf},
        json={
            "slug": f"case-builder-{uuid4().hex[:10]}",
            "content": {
                "title": "Case Builder fixture",
                "summary": "Initial projected authoring draft.",
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
                                "prompt": "Bu durumda en adil karar hangisidir?",
                                "response_type": "SINGLE_CHOICE",
                                "response_schema": {"options": ["Katılıyorum", "Katılmıyorum"]},
                            }
                        ],
                    }
                ],
            },
        },
    )
    assert response.status_code == 201
    return response.json()


def _enrich_projected_draft(app, version_id: UUID) -> None:
    repository = app.state.content_authoring_repository
    current = repository.get_version(version_id)
    assert current is not None
    enriched = replace(
        current,
        flow_template_code="STANDARD_WEIGH",
        flow_template_version_no=7,
        content_locale="tr",
        market_scope=MarketScope.COUNTRY_SET,
        country_codes=("TR", "DE"),
        cultural_context_note="Kültürel bağlam notu",
        legal_context_note="Hukuki bağlam notu",
        completed_review_modes=("SOURCE_VERIFY",),
        localizations=(
            AuthoringCaseLocalization(
                locale="en",
                title="Case Builder fixture",
                summary="English editorial summary.",
                question_prompts={"primary-question": "What is the fairest decision here?"},
                option_labels={
                    "primary-question": {
                        "Katılıyorum": "Agree",
                        "Katılmıyorum": "Disagree",
                    }
                },
            ),
        ),
    )
    app.state.content_authoring_service.save_draft(enriched)


def _draft_body(version: dict[str, object]) -> dict[str, object]:
    return {
        "title": version["title"],
        "summary": version["summary"],
        "base_format_code": version["base_format_code"],
        "primary_domain_code": version["primary_domain_code"],
        "content_risk": version["content_risk"],
        "issues": version["issues"],
        "context_blocks": version["context_blocks"],
        "sources": version["sources"],
        "modifiers": version["modifiers"],
        "is_fact_bearing": version["is_fact_bearing"],
        "is_real_event": version["is_real_event"],
        "required_review_modes": version["required_review_modes"],
        "content_locale": version["content_locale"],
        "market_scope": version["market_scope"],
        "country_codes": version["country_codes"],
        "cultural_context_note": version["cultural_context_note"],
        "legal_context_note": version["legal_context_note"],
        "localizations": version["localizations"],
    }


def test_case_builder_requires_editor_and_never_needs_csrf_for_read() -> None:
    app = create_app()
    editor, editor_csrf = _issue_admin(app, AdminRole.EDITOR)
    reviewer, _ = _issue_admin(app, AdminRole.REVIEWER)
    created = _create_case(editor, editor_csrf)
    version_id = created["id"]

    missing = TestClient(app).get(f"/internal/admin/v1/case-builder/case-versions/{version_id}")
    assert missing.status_code == 401

    denied = reviewer.get(f"/internal/admin/v1/case-builder/case-versions/{version_id}")
    assert denied.status_code == 403
    assert denied.json()["code"] == "ADMIN_FORBIDDEN"

    loaded = editor.get(f"/internal/admin/v1/case-builder/case-versions/{version_id}")
    assert loaded.status_code == 200
    assert loaded.json()["state"] == "DRAFT"


def test_case_builder_round_trip_preserves_flow_and_server_owned_review_state() -> None:
    app = create_app()
    editor, csrf = _issue_admin(app, AdminRole.EDITOR, AdminRole.REVIEWER)
    created = _create_case(editor, csrf)
    version_id = UUID(str(created["id"]))
    case_id = created["case_id"]
    _enrich_projected_draft(app, version_id)

    loaded = editor.get(f"/internal/admin/v1/case-builder/case-versions/{version_id}")
    assert loaded.status_code == 200
    body = loaded.json()
    assert body["flow_template_code"] == "STANDARD_WEIGH"
    assert body["flow_template_version_no"] == 7
    assert body["content_locale"] == "tr"
    assert body["market_scope"] == "COUNTRY_SET"
    assert body["country_codes"] == ["TR", "DE"]
    assert body["completed_review_modes"] == ["SOURCE_VERIFY"]
    assert body["localizations"][0]["option_labels"]["primary-question"] == {
        "Katılıyorum": "Agree",
        "Katılmıyorum": "Disagree",
    }

    draft = _draft_body(body)
    draft["title"] = "Editör tarafından güncellenen başlık"
    draft["summary"] = "Kaydedilmiş fakat henüz incelemeye gönderilmemiş taslak."
    draft["country_codes"] = ["TR"]
    draft["required_review_modes"] = ["EDITORIAL", "FACT_CHECK"]

    missing_csrf = editor.put(
        f"/internal/admin/v1/case-builder/case-versions/{version_id}",
        json=draft,
    )
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"

    saved = editor.put(
        f"/internal/admin/v1/case-builder/case-versions/{version_id}",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=draft,
    )
    assert saved.status_code == 200
    saved_body = saved.json()
    assert saved_body["state"] == "DRAFT"
    assert saved_body["title"] == draft["title"]
    assert saved_body["flow_template_code"] == "STANDARD_WEIGH"
    assert saved_body["flow_template_version_no"] == 7
    assert saved_body["completed_review_modes"] == ["SOURCE_VERIFY"]
    assert saved_body["country_codes"] == ["TR"]

    flow_override = dict(draft)
    flow_override["flow_template_code"] = "ATTACKER_FLOW"
    rejected_flow = editor.put(
        f"/internal/admin/v1/case-builder/case-versions/{version_id}",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=flow_override,
    )
    assert rejected_flow.status_code == 422

    review_override = dict(draft)
    review_override["completed_review_modes"] = ["EDITORIAL", "FACT_CHECK"]
    rejected_review_state = editor.put(
        f"/internal/admin/v1/case-builder/case-versions/{version_id}",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=review_override,
    )
    assert rejected_review_state.status_code == 422

    audit_before_submit = editor.get(f"/internal/admin/v1/cases/{case_id}/audit")
    assert audit_before_submit.status_code == 200
    assert [item["command"] for item in audit_before_submit.json()["items"]] == ["create_case"]

    submitted = editor.post(
        f"/internal/admin/v1/case-versions/{version_id}/submit",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert submitted.status_code == 200
    assert submitted.json()["state"] == "IN_REVIEW"

    audit_after_submit = editor.get(f"/internal/admin/v1/cases/{case_id}/audit")
    assert audit_after_submit.status_code == 200
    assert [item["command"] for item in audit_after_submit.json()["items"]] == [
        "create_case",
        "submit_for_review",
    ]


def test_case_builder_has_no_review_or_publication_mutations() -> None:
    app = create_app()
    editor, csrf = _issue_admin(app, AdminRole.EDITOR)
    created = _create_case(editor, csrf)
    version_id = created["id"]

    for command in ("approve", "reject", "publish", "withdraw"):
        response = editor.post(
            f"/internal/admin/v1/case-builder/case-versions/{version_id}/{command}",
            headers={ADMIN_CSRF_HEADER: csrf},
            json={"rationale": "must not exist"},
        )
        assert response.status_code == 404

    loaded = editor.get(f"/internal/admin/v1/case-builder/case-versions/{version_id}")
    rendered = str(loaded.json()).lower()
    for forbidden in (
        "raw_evidence_body",
        "provider_secret_ref",
        "storage_ref",
        "backend_object_key",
        "session_token",
        "csrf_token",
    ):
        assert forbidden not in rendered
