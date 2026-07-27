from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from fastapi.testclient import TestClient

from kefe_api.core.errors import DomainError
from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import (
    DEMO_CASE_ID,
    DEMO_CONFIDENCE_QUESTION_ID,
    DEMO_QUESTION_ID,
)


def _guest(client: TestClient) -> tuple[UUID, dict[str, str]]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    body = response.json()
    return UUID(body["actor_id"]), {"Authorization": f"Bearer {body['access_token']}"}


def _start(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions", headers=headers)
    assert response.status_code == 201
    return response.json()["session_id"]


def _answer(client: TestClient, session_id: str, headers: dict[str, str]) -> None:
    response = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    assert response.status_code == 200


def test_explore_lists_published_cases_without_identity() -> None:
    client = TestClient(create_app())
    response = client.get("/v1/cases?limit=1")
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["case_id"] == str(DEMO_CASE_ID)
    assert items[0]["base_format"] == "DILEMMA"
    assert "questions" not in items[0]
    assert "result" not in items[0]


def test_case_exposes_typed_question_contract_without_results() -> None:
    client = TestClient(create_app())
    response = client.get(f"/v1/cases/{DEMO_CASE_ID}")
    assert response.status_code == 200
    body = response.json()
    assert "result" not in body

    questions = {item["question_id"]: item for item in body["questions"]}
    decision = questions[str(DEMO_QUESTION_ID)]
    assert decision["response_type"] == "SINGLE_CHOICE"
    assert decision["required"] is True
    assert decision["response_schema"] == {"options": ["A", "B"]}

    confidence = questions[str(DEMO_CONFIDENCE_QUESTION_ID)]
    assert confidence["response_type"] == "CONFIDENCE"
    assert confidence["required"] is False
    assert confidence["response_schema"] == {"min": 1, "max": 5, "step": 1}


def test_guest_identity_is_required_for_decision_writes() -> None:
    client = TestClient(create_app())
    response = client.post(f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions")
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


def test_commit_first_happy_path() -> None:
    client = TestClient(create_app())
    _, headers = _guest(client)
    case = client.get(f"/v1/cases/{DEMO_CASE_ID}")
    assert case.status_code == 200
    assert "result" not in case.json()

    session_id = _start(client, headers)
    _answer(client, session_id, headers)

    commit = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": "commit-0001"},
    )
    assert commit.status_code == 200
    assert commit.json()["state"] == "COMMITTED"

    reveal = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=headers)
    assert reveal.status_code == 200
    assert reveal.json()["layer"] == "TRUSTED"
    assert reveal.json()["n"] > 0


def test_optional_confidence_can_be_saved_before_commit() -> None:
    client = TestClient(create_app())
    _, headers = _guest(client)
    session_id = _start(client, headers)
    response = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={
            "responses": [
                {"question_id": str(DEMO_QUESTION_ID), "value": "B"},
                {"question_id": str(DEMO_CONFIDENCE_QUESTION_ID), "value": 4},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["response_count"] == 2

    commit = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": "commit-confidence"},
    )
    assert commit.status_code == 200


def test_invalid_choice_and_confidence_are_rejected_by_schema() -> None:
    client = TestClient(create_app())
    _, headers = _guest(client)
    session_id = _start(client, headers)

    invalid_choice = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "C"}]},
    )
    assert invalid_choice.status_code == 422
    assert invalid_choice.json()["code"] == "WEIGH_RESPONSE_INVALID"

    invalid_confidence = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={
            "responses": [
                {"question_id": str(DEMO_CONFIDENCE_QUESTION_ID), "value": 6},
            ]
        },
    )
    assert invalid_confidence.status_code == 422
    assert invalid_confidence.json()["code"] == "WEIGH_RESPONSE_INVALID"


def test_reveal_before_commit_is_forbidden() -> None:
    client = TestClient(create_app())
    _, headers = _guest(client)
    session_id = _start(client, headers)
    response = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=headers)
    assert response.status_code == 403
    assert response.json()["code"] == "RESULT_COMMIT_REQUIRED"


def test_commit_is_idempotent_for_same_key() -> None:
    client = TestClient(create_app())
    _, headers = _guest(client)
    session_id = _start(client, headers)
    _answer(client, session_id, headers)
    commit_headers = {**headers, "Idempotency-Key": "commit-0002"}

    first = client.post(f"/v1/weigh-sessions/{session_id}/commit", headers=commit_headers)
    second = client.post(f"/v1/weigh-sessions/{session_id}/commit", headers=commit_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["committed_at"] == second.json()["committed_at"]


def test_different_key_after_commit_is_conflict() -> None:
    client = TestClient(create_app())
    _, headers = _guest(client)
    session_id = _start(client, headers)
    _answer(client, session_id, headers)
    first = {**headers, "Idempotency-Key": "commit-0003"}
    second = {**headers, "Idempotency-Key": "commit-0004"}

    assert client.post(f"/v1/weigh-sessions/{session_id}/commit", headers=first).status_code == 200
    response = client.post(f"/v1/weigh-sessions/{session_id}/commit", headers=second)
    assert response.status_code == 409
    assert response.json()["code"] == "WEIGH_SESSION_ALREADY_COMMITTED"


def test_incomplete_response_cannot_commit() -> None:
    client = TestClient(create_app())
    _, headers = _guest(client)
    session_id = _start(client, headers)
    response = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": "commit-0005"},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "WEIGH_RESPONSE_INCOMPLETE"


def test_session_is_actor_scoped() -> None:
    client = TestClient(create_app())
    _, owner_headers = _guest(client)
    _, other_headers = _guest(client)
    session_id = _start(client, owner_headers)
    response = client.get(f"/v1/weigh-sessions/{session_id}/reveal", headers=other_headers)
    assert response.status_code == 404
    assert response.json()["code"] == "WEIGH_SESSION_NOT_FOUND"


def test_response_update_after_commit_is_rejected() -> None:
    client = TestClient(create_app())
    _, headers = _guest(client)
    session_id = _start(client, headers)
    _answer(client, session_id, headers)
    commit = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": "commit-0006"},
    )
    assert commit.status_code == 200

    response = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "B"}]},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "WEIGH_SESSION_NOT_EDITABLE"


def test_competing_commits_linearize_to_one_commit_event() -> None:
    app = create_app()
    client = TestClient(app)
    actor_id, headers = _guest(client)
    session_id = UUID(_start(client, headers))
    _answer(client, str(session_id), headers)
    service = app.state.decision_service

    def attempt(key: str) -> str:
        try:
            service.commit(actor_id=actor_id, session_id=session_id, idempotency_key=key)
            return "COMMITTED"
        except DomainError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = set(executor.map(attempt, ("race-key-1", "race-key-2")))

    assert outcomes == {"COMMITTED", "WEIGH_SESSION_ALREADY_COMMITTED"}
    committed_events = [
        event
        for event in app.state.decision_repository.events
        if event["name"] == "weigh.committed"
    ]
    assert len(committed_events) == 1
