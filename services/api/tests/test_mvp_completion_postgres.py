from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID
from kefe_api.modules.identity.account_models import OtpChannel

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    app = create_app()
    return app, TestClient(app)


def _guest(client: TestClient) -> tuple[dict[str, str], str]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}, response.json()[
        "actor_id"
    ]


def _commit(client: TestClient, headers: dict[str, str], key: str) -> str:
    start = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    assert start.status_code == 201
    session_id = start.json()["session_id"]
    assert (
        client.put(
            f"/v1/weigh-sessions/{session_id}/responses",
            headers=headers,
            json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/v1/weigh-sessions/{session_id}/commit",
            headers={**headers, "Idempotency-Key": key},
        ).status_code
        == 200
    )
    return session_id


def _convert(app, client: TestClient, headers: dict[str, str], email: str) -> dict[str, object]:
    challenge = client.post(
        "/v1/auth/otp/request",
        json={"channel": "EMAIL", "identifier": email},
    )
    assert challenge.status_code == 201
    code = app.state.otp_delivery.code_for(channel=OtpChannel.EMAIL, identifier=email)
    assert code is not None
    verification = client.post(
        "/v1/auth/otp/verify",
        json={"challenge_id": challenge.json()["challenge_id"], "code": code},
    )
    assert verification.status_code == 200
    converted = client.post(
        "/v1/auth/guest-merge",
        headers=headers,
        json={"verification_token": verification.json()["verification_token"]},
    )
    assert converted.status_code == 200
    return converted.json()


def _assert_revoked(client: TestClient, headers: dict[str, str]) -> None:
    denied = client.get("/v1/me/progress", headers=headers)
    assert denied.status_code == 401
    assert denied.json()["code"] == "AUTH_TOKEN_REVOKED"


def test_postgres_existing_account_merge_preserves_product_history_and_controls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, client = _app(monkeypatch)
    database_url = os.environ["KEFE_DATABASE_URL"]
    email = "merge-mvp@example.test"

    account_guest_headers, account_guest_id = _guest(client)
    first_session = _commit(client, account_guest_headers, "mvp-account-first-0001")
    first_account = _convert(app, client, account_guest_headers, email)
    account_actor_id = first_account["actor_id"]
    account_headers = {"Authorization": f"Bearer {first_account['access_token']}"}
    _assert_revoked(client, account_guest_headers)
    assert client.get("/v1/me/progress", headers=account_headers).status_code == 200

    second_guest_headers, second_guest_id = _guest(client)
    second_session = _commit(client, second_guest_headers, "mvp-account-second-0001")
    share = client.post(
        "/v1/shares",
        headers=second_guest_headers,
        json={"session_id": second_session, "include_decision": False},
    )
    assert share.status_code == 201
    reason = client.post(
        f"/v1/weigh-sessions/{second_session}/community-reason",
        headers=second_guest_headers,
        json={"tags": ["FAIRNESS"]},
    )
    assert reason.status_code == 200

    merged = _convert(app, client, second_guest_headers, email)
    assert merged["actor_id"] == account_actor_id
    assert merged["merged_from_actor_id"] == second_guest_id
    merged_headers = {"Authorization": f"Bearer {merged['access_token']}"}
    _assert_revoked(client, second_guest_headers)

    # Existing destination-account sessions and the newly issued merge session both survive.
    assert client.get("/v1/me/progress", headers=account_headers).status_code == 200
    assert client.get("/v1/me/progress", headers=merged_headers).status_code == 200

    progress = client.get("/v1/me/progress", headers=merged_headers)
    assert progress.status_code == 200
    assert progress.json()["progress"]["meaningful_weigh_count"] == 2

    # Transferred Share remains revocable by the account actor after merge.
    assert (
        client.delete(
            f"/v1/shares/{share.json()['share_id']}",
            headers=merged_headers,
        ).status_code
        == 204
    )

    exported = client.get("/v1/me/privacy-export", headers=merged_headers)
    assert exported.status_code == 200
    exported_sessions = {
        item["session_id"] for item in exported.json()["product_data"]["weigh_sessions"]
    }
    assert {first_session, second_session} <= exported_sessions

    engine = create_engine(database_url)
    with engine.connect() as connection:
        merge_row = (
            connection.execute(
                text(
                    """
                SELECT guest_actor_id, account_actor_id
                FROM identity.actor_merge
                WHERE guest_actor_id = :guest_actor_id
                """
                ),
                {"guest_actor_id": second_guest_id},
            )
            .mappings()
            .one()
        )
        community_owner = connection.execute(
            text("SELECT actor_id FROM community.reason WHERE id = :id"),
            {"id": reason.json()["reason_id"]},
        ).scalar_one()
        active_merged_guest_sessions = connection.execute(
            text(
                """
                SELECT count(*)
                FROM identity.actor_session
                WHERE actor_id = :guest_actor_id
                  AND revoked_at IS NULL
                """
            ),
            {"guest_actor_id": second_guest_id},
        ).scalar_one()
    assert str(merge_row["account_actor_id"]) == account_actor_id
    assert str(merge_row["guest_actor_id"]) == second_guest_id
    assert str(community_owner) == account_actor_id
    assert account_guest_id == account_actor_id
    assert active_merged_guest_sessions == 0

    deleted = client.delete(
        "/v1/me",
        headers={**account_headers, "X-KEFE-Delete-Confirm": f"DELETE:{account_actor_id}"},
    )
    assert deleted.status_code == 200
    assert client.get("/v1/me/progress", headers=merged_headers).status_code == 401
    get_settings.cache_clear()
