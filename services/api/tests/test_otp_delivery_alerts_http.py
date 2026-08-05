from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminRole
from kefe_api.modules.admin_security.router import (
    ADMIN_CSRF_HEADER,
    ADMIN_SESSION_COOKIE,
)
from kefe_api.modules.identity.account_models import OtpChannel
from kefe_api.modules.identity.otp_delivery import (
    OtpDeliveryOperationalResult,
    OtpDeliveryOutcome,
)

ALERTS_ENDPOINT = "/internal/admin/v1/operational-reports/otp-delivery-alerts"
SNAPSHOT_ENDPOINT = "/internal/admin/v1/operational-reports/snapshot"


def _app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KEFE_OTP_DELIVERY_HEALTH_FAILURE_ATTENTION", "1")
    monkeypatch.setenv("KEFE_OTP_DELIVERY_HEALTH_FAILURE_CRITICAL", "2")
    monkeypatch.setenv("KEFE_OTP_DELIVERY_HEALTH_UNAVAILABLE_ATTENTION", "1")
    monkeypatch.setenv("KEFE_OTP_DELIVERY_HEALTH_UNAVAILABLE_CRITICAL", "2")
    monkeypatch.setenv("KEFE_OTP_DELIVERY_HEALTH_MINIMUM_RATIO_SAMPLE", "100")
    get_settings.cache_clear()
    return create_app()


def _issue_admin(app, role: AdminRole, *, step_up: bool = False):
    store = app.state.admin_session_store
    assert isinstance(store, InMemoryAdminSessionStore)
    subject_id = uuid4()
    store.upsert_subject(subject_id, roles=frozenset({role}))
    now = datetime.now(UTC)
    issued = store.issue(
        admin_subject_id=subject_id,
        authenticated_at=now,
        mfa_satisfied_at=now,
        expires_at=now + timedelta(hours=1),
    )
    if step_up:
        store.record_step_up(issued.session_id, step_up_at=now)
    client = TestClient(app)
    client.cookies.set(ADMIN_SESSION_COOKIE, issued.session_token)
    return client, issued, subject_id


def _seed_attention_candidate(app) -> str:
    app.state.otp_delivery_health_observer.record(
        OtpDeliveryOperationalResult(
            outcome=OtpDeliveryOutcome.UNAVAILABLE,
            channel=OtpChannel.EMAIL,
            attempts=1,
            status_code=503,
            error_code="OTP_PROVIDER_RETRYABLE_STATUS",
        )
    )
    records = app.state.otp_delivery_health_service.list_alert_candidates()
    assert len(records) == 1
    return str(records[0].candidate.id)


def _ack_endpoint(candidate_id: str) -> str:
    return f"{ALERTS_ENDPOINT}/{candidate_id}/acknowledgement"


def _ack_body(candidate_id: str) -> dict[str, str]:
    return {
        "expected_candidate_id": candidate_id,
        "acknowledgement": "ACKNOWLEDGE",
    }


def test_alert_list_requires_operational_report_read_and_is_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    candidate_id = _seed_attention_candidate(app)

    editor, _, _ = _issue_admin(app, AdminRole.EDITOR)
    denied = editor.get(ALERTS_ENDPOINT)
    assert denied.status_code == 403
    assert denied.json()["code"] == "ADMIN_FORBIDDEN"
    assert denied.json()["meta"]["required_capability"] == "OPERATIONAL_REPORT_READ"

    for role in (AdminRole.REVIEWER, AdminRole.PUBLISHER, AdminRole.ACCESS_ADMIN):
        client, _, _ = _issue_admin(app, role)
        response = client.get(ALERTS_ENDPOINT, params={"limit": 1, "offset": 0})
        assert response.status_code == 200
        assert response.json()["items"][0]["candidate_id"] == candidate_id

    assert editor.get(ALERTS_ENDPOINT, params={"limit": 101}).status_code == 422
    assert editor.put(ALERTS_ENDPOINT).status_code == 405
    assert editor.delete(ALERTS_ENDPOINT).status_code == 405
    get_settings.cache_clear()


def test_acknowledgement_requires_capability_csrf_step_up_and_exact_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    candidate_id = _seed_attention_candidate(app)
    endpoint = _ack_endpoint(candidate_id)

    publisher, publisher_issue, _ = _issue_admin(
        app,
        AdminRole.PUBLISHER,
        step_up=True,
    )
    publisher_denied = publisher.post(
        endpoint,
        json=_ack_body(candidate_id),
        headers={ADMIN_CSRF_HEADER: publisher_issue.csrf_token},
    )
    assert publisher_denied.status_code == 403
    assert publisher_denied.json()["code"] == "ADMIN_FORBIDDEN"
    assert publisher_denied.json()["meta"]["required_capability"] == (
        "OPERATIONAL_ALERT_ACKNOWLEDGE"
    )

    reviewer, reviewer_issue, _ = _issue_admin(app, AdminRole.REVIEWER)
    no_csrf = reviewer.post(endpoint, json=_ack_body(candidate_id))
    assert no_csrf.status_code == 403
    assert no_csrf.json()["code"] == "ADMIN_CSRF_REQUIRED"

    no_step_up = reviewer.post(
        endpoint,
        json=_ack_body(candidate_id),
        headers={ADMIN_CSRF_HEADER: reviewer_issue.csrf_token},
    )
    assert no_step_up.status_code == 403
    assert no_step_up.json()["code"] == "ADMIN_STEP_UP_REQUIRED"

    store = app.state.admin_session_store
    store.record_step_up(reviewer_issue.session_id, step_up_at=datetime.now(UTC))
    mismatch_id = str(uuid4())
    mismatch = reviewer.post(
        endpoint,
        json=_ack_body(mismatch_id),
        headers={ADMIN_CSRF_HEADER: reviewer_issue.csrf_token},
    )
    assert mismatch.status_code == 409
    assert mismatch.json()["code"] == "ADMIN_OPERATIONAL_ALERT_ACK_MISMATCH"

    extra_text = reviewer.post(
        endpoint,
        json={**_ack_body(candidate_id), "note": "resolved by operator"},
        headers={ADMIN_CSRF_HEADER: reviewer_issue.csrf_token},
    )
    assert extra_text.status_code == 422
    get_settings.cache_clear()


def test_acknowledgement_is_idempotent_privacy_safe_and_not_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    candidate_id = _seed_attention_candidate(app)
    reviewer, issued, subject_id = _issue_admin(
        app,
        AdminRole.REVIEWER,
        step_up=True,
    )
    endpoint = _ack_endpoint(candidate_id)
    headers = {ADMIN_CSRF_HEADER: issued.csrf_token}

    first = reviewer.post(endpoint, json=_ack_body(candidate_id), headers=headers)
    replay = reviewer.post(endpoint, json=_ack_body(candidate_id), headers=headers)
    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()

    body = first.json()
    assert body["acknowledged"] is True
    assert body["acknowledged_by_actor_ref"] == f"admin:{subject_id}"
    assert body["acknowledgement_is_resolution"] is False
    assert body["signal"] == "ATTENTION"

    filtered = reviewer.get(ALERTS_ENDPOINT, params={"acknowledged": True})
    assert filtered.status_code == 200
    assert [item["candidate_id"] for item in filtered.json()["items"]] == [candidate_id]
    assert filtered.json()["acknowledgement_is_resolution"] is False

    rendered = str(filtered.json()).lower()
    for forbidden in (
        "recipient",
        "destination",
        "destination_hash",
        "otp_code",
        "challenge_id",
        "delivery_id",
        "account_id",
        "user_id",
        "device_id",
        "provider_request_body",
        "provider_response_body",
        "credential",
        "secret_ref",
        "endpoint",
    ):
        assert forbidden not in rendered
    get_settings.cache_clear()


def test_snapshot_read_never_creates_alert_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    reviewer, _, _ = _issue_admin(app, AdminRole.REVIEWER)
    before = app.state.otp_delivery_health_service.list_alert_candidates()
    response = reviewer.get(SNAPSHOT_ENDPOINT)
    after = app.state.otp_delivery_health_service.list_alert_candidates()
    assert response.status_code == 200
    assert before == after == ()
    get_settings.cache_clear()


def test_acknowledging_unknown_candidate_returns_registered_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = _app(monkeypatch)
    reviewer, issued, _ = _issue_admin(app, AdminRole.ACCESS_ADMIN, step_up=True)
    candidate_id = str(uuid4())
    response = reviewer.post(
        _ack_endpoint(candidate_id),
        json=_ack_body(candidate_id),
        headers={ADMIN_CSRF_HEADER: issued.csrf_token},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "ADMIN_OPERATIONAL_ALERT_NOT_FOUND"
    get_settings.cache_clear()
