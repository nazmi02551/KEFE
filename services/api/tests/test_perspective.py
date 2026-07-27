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


def _answer_and_commit(
    client: TestClient,
    headers: dict[str, str],
    session_id: str,
    value: str,
) -> None:
    answer = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": value}]},
    )
    assert answer.status_code == 200
    commit = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": f"perspective-{value}-0001"},
    )
    assert commit.status_code == 200


def test_perspectives_are_hidden_before_commit() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    session_id = _start(client, headers)

    response = client.get(
        f"/v1/weigh-sessions/{session_id}/perspectives",
        headers=headers,
    )

    assert response.status_code == 403
    assert response.json()["code"] == "PERSPECTIVE_COMMIT_REQUIRED"


def test_committed_choice_receives_only_opposing_editorial_human_perspective() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    session_id = _start(client, headers)
    _answer_and_commit(client, headers, session_id, "A")

    response = client.get(
        f"/v1/weigh-sessions/{session_id}/perspectives",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["question_id"] == str(DEMO_QUESTION_ID)
    assert body["viewer_value"] == "A"
    assert body["selection_policy"] == "EDITORIAL_OPPOSITION_V1"
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["target_value"] == "B"
    assert item["source_kind"] == "EDITORIAL_HUMAN"
    assert item["moderation_state"] == "ALLOWED"


def test_private_user_reason_is_not_exposed_by_perspective_read_model() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    session_id = _start(client, headers)
    answer = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "B"}]},
    )
    assert answer.status_code == 200
    reason = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"tags": ["FAIRNESS"], "text": "Bu benim özel gerekçem."},
    )
    assert reason.status_code == 200

    commit = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": "perspective-private-0001"},
    )
    assert commit.status_code == 200

    response = client.get(
        f"/v1/weigh-sessions/{session_id}/perspectives",
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["target_value"] == "A"
    assert "Bu benim özel gerekçem." not in response.text
    assert "PRIVATE" not in response.text
