from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from fastapi.testclient import TestClient

from kefe_api.core.errors import DomainError
from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID

ACTOR_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
HEADERS = {"X-Actor-Id": str(ACTOR_ID)}


def _start(client: TestClient) -> str:
    response = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=HEADERS)
    assert response.status_code == 201
    return response.json()["session_id"]


def _answer(client: TestClient, session_id: str) -> None:
    response = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=HEADERS,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    assert response.status_code == 200


def test_commit_first_happy_path() -> None:
    client = TestClient(create_app())
    case = client.get(f"/v1/cases/{DEMO_CASE_ID}")
    assert case.status_code == 200
    assert "result" not in case.json()

    session_id = _start(client)
    _answer(client, session_id)

    commit = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**HEADERS, "Idempotency-Key": "commit-0001"},
    )
    assert commit.status_code == 200
    assert commit.json()["state"] == "COMMITTED"

    reveal = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=HEADERS)
    assert reveal.status_code == 200
    assert reveal.json()["layer"] == "TRUSTED"
    assert reveal.json()["n"] > 0


def test_reveal_before_commit_is_forbidden() -> None:
    client = TestClient(create_app())
    session_id = _start(client)
    response = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=HEADERS)
    assert response.status_code == 403
    assert response.json()["code"] == "RESULT_COMMIT_REQUIRED"


def test_commit_is_idempotent_for_same_key() -> None:
    client = TestClient(create_app())
    session_id = _start(client)
    _answer(client, session_id)
    headers = {**HEADERS, "Idempotency-Key": "commit-0002"}

    first = client.post(f"/v1/weigh-sessions/{session_id}/commit", headers=headers)
    second = client.post(f"/v1/weigh-sessions/{session_id}/commit", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["committed_at"] == second.json()["committed_at"]


def test_different_key_after_commit_is_conflict() -> None:
    client = TestClient(create_app())
    session_id = _start(client)
    _answer(client, session_id)
    first = {**HEADERS, "Idempotency-Key": "commit-0003"}
    second = {**HEADERS, "Idempotency-Key": "commit-0004"}

    assert client.post(f"/v1/weigh-sessions/{session_id}/commit", headers=first).status_code == 200
    response = client.post(f"/v1/weigh-sessions/{session_id}/commit", headers=second)
    assert response.status_code == 409
    assert response.json()["code"] == "WEIGH_SESSION_ALREADY_COMMITTED"


def test_incomplete_response_cannot_commit() -> None:
    client = TestClient(create_app())
    session_id = _start(client)
    response = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**HEADERS, "Idempotency-Key": "commit-0005"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "WEIGH_RESPONSE_INCOMPLETE"


def test_session_is_actor_scoped() -> None:
    client = TestClient(create_app())
    session_id = _start(client)
    other_actor = {"X-Actor-Id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"}
    response = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=other_actor)
    assert response.status_code == 404
    assert response.json()["code"] == "WEIGH_SESSION_NOT_FOUND"


def test_response_update_after_commit_is_rejected() -> None:
    client = TestClient(create_app())
    session_id = _start(client)
    _answer(client, session_id)
    commit = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**HEADERS, "Idempotency-Key": "commit-0006"},
    )
    assert commit.status_code == 200

    response = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=HEADERS,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "B"}]},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "WEIGH_SESSION_NOT_EDITABLE"


def test_competing_commits_linearize_to_one_commit_event() -> None:
    app = create_app()
    client = TestClient(app)
    session_id = UUID(_start(client))
    _answer(client, str(session_id))
    service = app.state.decision_service

    def attempt(key: str) -> str:
        try:
            service.commit(actor_id=ACTOR_ID, session_id=session_id, idempotency_key=key)
            return "COMMITTED"
        except DomainError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = set(executor.map(attempt, ("race-key-1", "race-key-2")))

    assert outcomes == {"COMMITTED", "WEIGH_SESSION_ALREADY_COMMITTED"}
    committed_events = [
        event for event in app.state.decision_repository.events if event["name"] == "weigh.committed"
    ]
    assert len(committed_events) == 1
