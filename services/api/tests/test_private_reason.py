from uuid import UUID

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID


def _guest(client: TestClient) -> dict[str, str]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _start(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    assert response.status_code == 201
    return response.json()["session_id"]


def _answer_and_commit(client: TestClient, session_id: str, headers: dict[str, str]) -> None:
    answer = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    assert answer.status_code == 200
    commit = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": "reason-test-commit"},
    )
    assert commit.status_code == 200


def test_private_reason_accepts_schema_tags_and_marks_text_pending() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    session_id = _start(client, headers)

    response = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={
            "tags": ["fairness", "need", "fairness"],
            "text": "İki kişinin ihtiyacını birlikte değerlendirdim.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["tags"] == ["FAIRNESS", "NEED"]
    assert body["moderation_state"] == "PENDING"
    assert body["visibility"] == "PRIVATE"


def test_tags_only_reason_does_not_require_text_moderation() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    session_id = _start(client, headers)

    response = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"tags": ["RESPONSIBILITY"]},
    )

    assert response.status_code == 200
    assert response.json()["moderation_state"] == "NOT_REQUIRED"


def test_reason_rejects_unknown_tags_and_empty_payload() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    session_id = _start(client, headers)

    unknown = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"tags": ["IDEOLOGY"]},
    )
    assert unknown.status_code == 422
    assert unknown.json()["code"] == "REASON_TAG_INVALID"

    empty = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"tags": [], "text": "   "},
    )
    assert empty.status_code == 422
    assert empty.json()["code"] == "REASON_EMPTY"


def test_reason_is_immutable_after_commit() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    session_id = _start(client, headers)

    initial = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"tags": ["FAIRNESS"]},
    )
    assert initial.status_code == 200
    _answer_and_commit(client, session_id, headers)

    update = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"tags": ["NEED"]},
    )
    assert update.status_code == 409
    assert update.json()["code"] == "WEIGH_SESSION_NOT_EDITABLE"


def test_reason_is_actor_scoped() -> None:
    client = TestClient(create_app())
    owner_headers = _guest(client)
    other_headers = _guest(client)
    session_id = _start(client, owner_headers)

    response = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=other_headers,
        json={"tags": ["FAIRNESS"]},
    )
    assert response.status_code == 404
    assert response.json()["code"] == "WEIGH_SESSION_NOT_FOUND"
    UUID(session_id)
