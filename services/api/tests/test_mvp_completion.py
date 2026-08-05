from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.community_reason.models import CommunityReasonModeration
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID
from kefe_api.modules.identity.account_models import OtpChannel


def _guest(client: TestClient) -> dict[str, str]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _start_and_answer(client: TestClient, headers: dict[str, str]) -> str:
    start = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    assert start.status_code == 201
    session_id = start.json()["session_id"]
    answer = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    assert answer.status_code == 200
    return session_id


def _commit(client: TestClient, headers: dict[str, str], session_id: str) -> None:
    commit = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": f"mvp-completion-{session_id}"},
    )
    assert commit.status_code == 200


def _committed(client: TestClient, headers: dict[str, str]) -> str:
    session_id = _start_and_answer(client, headers)
    _commit(client, headers, session_id)
    return session_id


def test_account_offer_is_functional_and_guest_history_survives_conversion() -> None:
    app = create_app()
    client = TestClient(app)
    guest_headers = _guest(client)
    session_id = _committed(client, guest_headers)

    progress = client.get("/v1/me/progress", headers=guest_headers)
    assert progress.status_code == 200
    assert progress.json()["account_offer"]["account_creation_available"] is True

    identifier = "mvp@example.test"
    challenge = client.post(
        "/v1/auth/otp/request",
        json={"channel": "EMAIL", "identifier": identifier},
    )
    assert challenge.status_code == 201
    body = challenge.json()
    assert body["destination_hint"] == "mv***@example.test"
    code = app.state.otp_delivery.code_for(
        channel=OtpChannel.EMAIL,
        identifier=identifier,
    )
    assert code is not None

    verified = client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": body["challenge_id"], "code": code},
    )
    assert verified.status_code == 200
    converted = client.post(
        "/v1/auth/guest-merge",
        headers=guest_headers,
        json={"verification_token": verified.json()["verification_token"]},
    )
    assert converted.status_code == 200
    account_headers = {"Authorization": f"Bearer {converted.json()['access_token']}"}

    after = client.get("/v1/me/progress", headers=account_headers)
    assert after.status_code == 200
    assert after.json()["progress"]["meaningful_weigh_count"] == 1
    assert after.json()["progress"]["recent_cases"][0]["case_id"] == str(DEMO_CASE_ID)
    assert after.json()["account_offer"]["eligible"] is False
    assert after.json()["account_offer"]["account_creation_available"] is False

    old_token_progress = client.get("/v1/me/progress", headers=guest_headers)
    assert old_token_progress.status_code == 200
    assert old_token_progress.json()["progress"]["meaningful_weigh_count"] == 1
    assert session_id


def test_share_requires_commit_is_case_only_and_can_be_revoked() -> None:
    app = create_app()
    client = TestClient(app)
    headers = _guest(client)
    session_id = _start_and_answer(client, headers)

    denied = client.post(
        "/v1/shares",
        headers=headers,
        json={"session_id": session_id, "include_decision": True},
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == "SHARE_COMMIT_REQUIRED"

    reason = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"tags": ["FAIRNESS"], "text": "private reason must never leak"},
    )
    assert reason.status_code == 200
    _commit(client, headers, session_id)

    unsupported = client.post(
        "/v1/shares",
        headers=headers,
        json={"session_id": session_id, "include_decision": True},
    )
    assert unsupported.status_code == 422
    assert unsupported.json()["code"] == "SHARE_DECISION_EXPOSURE_NOT_SUPPORTED"

    created = client.post(
        "/v1/shares",
        headers=headers,
        json={"session_id": session_id, "include_decision": False},
    )
    assert created.status_code == 201
    assert created.json()["include_decision"] is False
    public = client.get(f"/v1/shares/{created.json()['token']}")
    assert public.status_code == 200
    public_body = public.json()
    assert public_body["case_id"] == str(DEMO_CASE_ID)
    serialized = str(public_body).lower()
    assert "decision" not in serialized
    assert "confidence" not in serialized
    assert "private" not in serialized
    assert "reason" not in serialized

    revoked = client.delete(
        f"/v1/shares/{created.json()['share_id']}",
        headers=headers,
    )
    assert revoked.status_code == 204
    missing = client.get(f"/v1/shares/{created.json()['token']}")
    assert missing.status_code == 404


def test_community_reason_is_explicit_moderated_and_commit_gated_for_read() -> None:
    app = create_app()
    client = TestClient(app)
    headers = _guest(client)
    uncommitted_session_id = _start_and_answer(client, headers)

    pre_commit = client.get(
        f"/v1/weigh-sessions/{uncommitted_session_id}/community-reasons",
        headers=headers,
    )
    assert pre_commit.status_code == 403
    assert pre_commit.json()["code"] == "COMMUNITY_REASON_COMMIT_REQUIRED"

    session_id = _committed(client, headers)
    unauthenticated = client.get(f"/v1/weigh-sessions/{session_id}/community-reasons")
    assert unauthenticated.status_code == 401

    tags_only = client.post(
        f"/v1/weigh-sessions/{session_id}/community-reason",
        headers=headers,
        json={"tags": ["FAIRNESS", "NEED"]},
    )
    assert tags_only.status_code == 200
    assert tags_only.json()["moderation_state"] == "NOT_REQUIRED"

    snapshot = client.get(
        f"/v1/weigh-sessions/{session_id}/community-reasons",
        headers=headers,
    )
    assert snapshot.status_code == 200
    assert snapshot.json()["sample_size"] == 1
    assert snapshot.json()["tag_pattern_counts"] == {"FAIRNESS": 1, "NEED": 1}

    pending = client.post(
        f"/v1/weigh-sessions/{session_id}/community-reason",
        headers=headers,
        json={"tags": ["RESPONSIBILITY"], "text": "This must wait for moderation"},
    )
    assert pending.status_code == 200
    assert pending.json()["moderation_state"] == "PENDING"
    hidden = client.get(
        f"/v1/weigh-sessions/{session_id}/community-reasons",
        headers=headers,
    )
    assert hidden.status_code == 200
    assert hidden.json()["sample_size"] == 0

    reason_id = pending.json()["reason_id"]
    allowed = app.state.community_reason_service.moderate(
        reason_id=UUID(reason_id),
        state=CommunityReasonModeration.ALLOWED,
        actor_ref="test:mvp-completion",
        rationale="Explicit test moderation permits the submitted reason.",
    )
    assert allowed.reason.moderation_state.value == "ALLOWED"
    visible = client.get(
        f"/v1/weigh-sessions/{session_id}/community-reasons",
        headers=headers,
    )
    assert visible.status_code == 200
    assert visible.json()["sample_size"] == 1
    assert visible.json()["items"][0]["text"] == "This must wait for moderation"


def test_privacy_export_excludes_credentials_then_delete_revokes_identity() -> None:
    app = create_app()
    client = TestClient(app)
    headers = _guest(client)
    session_id = _start_and_answer(client, headers)
    reason = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"tags": ["FAIRNESS"], "text": "owner-visible private reason"},
    )
    assert reason.status_code == 200
    _commit(client, headers, session_id)

    exported = client.get("/v1/me/privacy-export", headers=headers)
    assert exported.status_code == 200
    body = exported.json()
    assert body["product_data"]["weigh_sessions"][0]["session_id"] == session_id
    assert body["product_data"]["private_reasons"][0]["text"] == ("owner-visible private reason")
    serialized = str(body).lower()
    assert "token_hash" not in serialized
    assert "access_token" not in serialized

    unconfirmed = client.delete("/v1/me", headers=headers)
    assert unconfirmed.status_code == 422
    deleted = client.delete(
        "/v1/me",
        headers={**headers, "X-KEFE-Delete-Confirm": f"DELETE:{body['actor_id']}"},
    )
    assert deleted.status_code == 200
    assert deleted.json()["private_data_deleted"] is True
    after = client.get("/v1/me/progress", headers=headers)
    assert after.status_code == 401
