from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import ADMIN_CSRF_HEADER, ADMIN_SESSION_COOKIE
from kefe_api.modules.knowledge.public_feed_manual_capture import (
    ApprovedPublicFeedManualCaptureService,
)
from kefe_api.modules.knowledge.source_acquisition import (
    SourceAcquisitionOutcome,
    SourceAcquisitionResult,
)


def _issue_admin(
    app,
    *roles: AdminRole,
    step_up: bool = False,
) -> tuple[TestClient, UUID, str, str]:
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
    if step_up:
        store.record_step_up(issued.session_id, step_up_at=now)
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, subject_id, issued.session_token, issued.csrf_token


def _catalog_payload() -> dict[str, object]:
    return {
        "feed_code": "test.http_manual_feed.v1",
        "display_name": "HTTP Manual Feed",
        "adapter_code": "test.http_manual_rss.v1",
        "external_locator": "https://http-manual.example.test/feed.xml",
        "parser_profile": {
            "accepted_media_types": [
                "application/atom+xml",
                "application/rss+xml",
                "application/xml",
                "text/xml",
            ],
            "max_document_bytes": 1_048_576,
            "max_elements": 4096,
            "max_depth": 16,
            "max_items": 256,
            "max_node_text_chars": 16_384,
            "max_total_text_chars": 262_144,
            "max_attributes_per_element": 8,
            "max_total_attribute_chars": 65_536,
            "max_metadata_field_chars": 4096,
        },
        "connect_timeout_ms": 1000,
        "read_timeout_ms": 1500,
        "total_timeout_ms": 3000,
        "max_response_bytes": 1_048_576,
        "max_redirect_hops": 1,
        "terms_evidence_ref": "evidence://terms/http-manual-v1",
        "rate_limit_evidence_ref": "evidence://rate/http-manual-v1",
        "quota_limit": 20,
        "quota_window_seconds": 60,
        "failure_threshold": 3,
        "circuit_open_seconds": 120,
        "permit_ttl_seconds": 30,
        "language_code": "en",
        "jurisdiction_code": "GLOBAL",
    }


class RecordingRuntime:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, *, definition, trace_id, at):
        self.calls.append((definition, trace_id, at))
        command = definition.acquisition_command()
        return SourceAcquisitionResult(
            outcome=SourceAcquisitionOutcome.BLOCKED,
            adapter_code=definition.adapter_code,
            pipeline_code=command.pipeline_code,
            pipeline_version=command.pipeline_version,
            trace_id=trace_id,
            duration_ms=5,
            error_code="TEST_MANUAL_CAPTURE_BLOCKED",
        )


def _replace_runtime(app, runtime: RecordingRuntime) -> None:
    app.state.public_feed_manual_capture_service = (
        ApprovedPublicFeedManualCaptureService(
            catalog=app.state.public_feed_catalog_repository,
            runtime=runtime,
            audit=app.state.public_feed_manual_capture_audit_repository,
            security=app.state.admin_security_service,
        )
    )


def _register_and_approve(app, client: TestClient, csrf: str) -> str:
    created = client.post(
        "/internal/admin/v1/public-feeds",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_catalog_payload(),
    )
    assert created.status_code == 201
    entry_id = created.json()["id"]
    approved = client.post(
        f"/internal/admin/v1/public-feeds/{entry_id}/approve-manual-capture",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert approved.status_code == 200
    assert approved.json()["state"] == "MANUAL_CAPTURE_APPROVED"
    return entry_id


def test_manual_capture_requires_session_csrf_capability_and_step_up() -> None:
    app = create_app()
    runtime = RecordingRuntime()
    _replace_runtime(app, runtime)
    anonymous = TestClient(app)
    entry_id = uuid4()
    assert anonymous.post(
        f"/internal/admin/v1/public-feeds/{entry_id}/capture-once"
    ).status_code == 401

    editor, _, _, editor_csrf = _issue_admin(
        app,
        AdminRole.EDITOR,
        step_up=True,
    )
    forbidden = editor.post(
        f"/internal/admin/v1/public-feeds/{entry_id}/capture-once",
        headers={ADMIN_CSRF_HEADER: editor_csrf},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "ADMIN_FORBIDDEN"

    reviewer, _, session_token, csrf = _issue_admin(app, AdminRole.REVIEWER)
    created = reviewer.post(
        "/internal/admin/v1/public-feeds",
        headers={ADMIN_CSRF_HEADER: csrf},
        json=_catalog_payload(),
    )
    assert created.status_code == 201
    catalog_entry_id = created.json()["id"]

    missing_csrf = reviewer.post(
        f"/internal/admin/v1/public-feeds/{catalog_entry_id}/capture-once"
    )
    assert missing_csrf.status_code == 403
    assert missing_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"

    no_step_up = reviewer.post(
        f"/internal/admin/v1/public-feeds/{catalog_entry_id}/capture-once",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert no_step_up.status_code == 403
    assert no_step_up.json()["code"] == "ADMIN_STEP_UP_REQUIRED"

    principal = app.state.admin_session_store.resolve(session_token).principal
    assert principal is not None
    app.state.admin_session_store.record_step_up(
        principal.session_id,
        step_up_at=datetime.now(UTC),
    )
    not_approved = reviewer.post(
        f"/internal/admin/v1/public-feeds/{catalog_entry_id}/capture-once",
        headers={ADMIN_CSRF_HEADER: csrf},
    )
    assert not_approved.status_code == 409
    assert not_approved.json()["code"] == (
        "PUBLIC_FEED_MANUAL_CAPTURE_NOT_APPROVED"
    )
    assert runtime.calls == []


def test_approved_capture_uses_header_trace_and_returns_bounded_result() -> None:
    app = create_app()
    runtime = RecordingRuntime()
    _replace_runtime(app, runtime)
    reviewer, subject_id, _, csrf = _issue_admin(
        app,
        AdminRole.REVIEWER,
        step_up=True,
    )
    entry_id = _register_and_approve(app, reviewer, csrf)

    response = reviewer.post(
        f"/internal/admin/v1/public-feeds/{entry_id}/capture-once",
        headers={
            ADMIN_CSRF_HEADER: csrf,
            "X-KEFE-Trace-ID": "trace-http-manual",
        },
        json={
            "external_locator": "https://attacker.example.test/private",
            "adapter_code": "attacker.adapter.v1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["catalog_entry_id"] == entry_id
    assert body["feed_code"] == "test.http_manual_feed.v1"
    assert body["trace_id"] == "trace-http-manual"
    assert body["outcome"] == "BLOCKED"
    assert body["error_code"] == "TEST_MANUAL_CAPTURE_BLOCKED"
    assert "external_locator" not in body
    assert "secret_ref" not in body
    assert "headers" not in body
    assert len(runtime.calls) == 1
    definition, trace_id, _ = runtime.calls[0]
    assert definition.external_locator == "https://http-manual.example.test/feed.xml"
    assert definition.adapter_code == "test.http_manual_rss.v1"
    assert trace_id == "trace-http-manual"

    audit = reviewer.get(
        f"/internal/admin/v1/public-feeds/{entry_id}/capture-audit"
    )
    assert audit.status_code == 200
    events = audit.json()["items"]
    assert [item["outcome"] for item in events] == [
        "ATTEMPT_STARTED",
        "BLOCKED",
    ]
    assert events[0]["actor_ref"] == f"admin:{subject_id}"
    assert all("external_locator" not in item for item in events)
    assert all("secret_ref" not in item for item in events)

    global_audit = reviewer.get(
        "/internal/admin/v1/public-feeds/capture-audit"
    )
    assert global_audit.status_code == 200
    assert global_audit.json() == audit.json()


def test_invalid_trace_is_rejected_before_runtime_or_audit() -> None:
    app = create_app()
    runtime = RecordingRuntime()
    _replace_runtime(app, runtime)
    reviewer, _, _, csrf = _issue_admin(
        app,
        AdminRole.REVIEWER,
        step_up=True,
    )
    entry_id = _register_and_approve(app, reviewer, csrf)

    invalid = reviewer.post(
        f"/internal/admin/v1/public-feeds/{entry_id}/capture-once",
        headers={
            ADMIN_CSRF_HEADER: csrf,
            "X-KEFE-Trace-ID": "contains spaces",
        },
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "PUBLIC_FEED_MANUAL_CAPTURE_TRACE_INVALID"
    assert runtime.calls == []
    audit = reviewer.get(
        f"/internal/admin/v1/public-feeds/{entry_id}/capture-audit"
    )
    assert audit.status_code == 200
    assert audit.json()["items"] == []
