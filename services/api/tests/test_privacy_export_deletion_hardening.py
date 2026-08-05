from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID


def _guest(client: TestClient) -> tuple[dict[str, str], UUID]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    return (
        {"Authorization": f"Bearer {response.json()['access_token']}"},
        UUID(response.json()["actor_id"]),
    )


def _commit(client: TestClient, headers: dict[str, str]) -> str:
    start = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    assert start.status_code == 201
    session_id = start.json()["session_id"]
    answer = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    assert answer.status_code == 200
    reason = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"tags": ["FAIRNESS"], "text": "owner-only deterministic export"},
    )
    assert reason.status_code == 200
    committed = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": f"privacy-{session_id}"},
    )
    assert committed.status_code == 200
    return session_id


def _digest(body: dict[str, object]) -> str:
    canonical = {
        "schema_version": body["schema_version"],
        "actor_id": body["actor_id"],
        "actor_kind": body["actor_kind"],
        "retention": body["retention"],
        "manifest": body["manifest"],
        "product_data": body["product_data"],
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_export_is_versioned_manifested_and_digest_deterministic() -> None:
    app = create_app()
    client = TestClient(app)
    headers, actor_id = _guest(client)
    session_id = _commit(client, headers)

    first = client.get("/v1/me/privacy-export", headers=headers)
    second = client.get("/v1/me/privacy-export", headers=headers)
    assert first.status_code == second.status_code == 200
    body = first.json()
    replay = second.json()

    assert body["schema_version"] == "privacy-export.v2"
    assert body["actor_id"] == str(actor_id)
    assert body["product_data"]["weigh_sessions"][0]["session_id"] == session_id
    assert body["manifest"]["dataset_counts"] == {
        "private_reasons": 1,
        "weigh_sessions": 1,
    }
    assert body["manifest"]["total_records"] == 2
    assert body["manifest"]["empty_datasets"] == []
    assert list(body["manifest"]["dataset_counts"]) == sorted(body["manifest"]["dataset_counts"])
    assert body["data_sha256"] == _digest(body)
    assert replay["data_sha256"] == body["data_sha256"]
    assert replay["manifest"] == body["manifest"]
    serialized = json.dumps(body).lower()
    assert "access_token" not in serialized
    assert "token_hash" not in serialized


def test_delete_requires_exact_actor_bound_confirmation() -> None:
    app = create_app()
    client = TestClient(app)
    headers, actor_id = _guest(client)

    assert client.delete("/v1/me", headers=headers).status_code == 422
    assert (
        client.delete(
            "/v1/me",
            headers={**headers, "X-KEFE-Delete-Confirm": "DELETE"},
        ).status_code
        == 422
    )
    assert (
        client.delete(
            "/v1/me",
            headers={
                **headers,
                "X-KEFE-Delete-Confirm": f"DELETE:{uuid4()}",
            },
        ).status_code
        == 422
    )

    deleted = client.delete(
        "/v1/me",
        headers={
            **headers,
            "X-KEFE-Delete-Confirm": f"DELETE:{actor_id}",
        },
    )
    assert deleted.status_code == 200
    assert deleted.json()["actor_id"] == str(actor_id)
    assert deleted.json()["actor_kind"] == "GUEST"
    assert deleted.json()["policy_version"] == "PRIVACY_SELF_SERVICE_V2"
    assert client.get("/v1/me/progress", headers=headers).status_code == 401


def test_memory_concurrent_deletion_converges_and_removes_merge_alias() -> None:
    app = create_app()
    identity = app.state.identity_repository
    repository = app.state.privacy_repository
    guest_actor_id = uuid4()
    account_actor_id = uuid4()
    expiry = datetime.now(UTC) + timedelta(days=1)
    identity.create_guest_session(
        actor_id=guest_actor_id,
        token_hash="guest-token-hash",
        expires_at=expiry,
    )
    identity.create_account_session(
        actor_id=account_actor_id,
        token_hash="account-token-hash",
        expires_at=expiry,
    )
    identity.promote_or_merge_actor(
        guest_actor_id=guest_actor_id,
        account_actor_id=account_actor_id,
    )
    assert identity._merged_into[guest_actor_id] == account_actor_id

    times = [datetime(2026, 8, 5, 10, 0, tzinfo=UTC), datetime(2026, 8, 5, 10, 1, tzinfo=UTC)]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                repository.delete_actor_data,
                actor_id=account_actor_id,
                actor_kind="ACCOUNT",
                deleted_at=deleted_at,
            )
            for deleted_at in times
        ]
    receipts = [future.result() for future in futures]

    assert receipts[0] == receipts[1]
    assert receipts[0].policy_version == "PRIVACY_SELF_SERVICE_V2"
    assert len(repository._receipts) == 1
    assert guest_actor_id not in identity._merged_into
    assert account_actor_id not in identity._merged_into.values()
