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


def _commit(client: TestClient, session_id: str, headers: dict[str, str]) -> None:
    answer = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={"responses": [{"question_id": str(DEMO_QUESTION_ID), "value": "A"}]},
    )
    assert answer.status_code == 200
    commit = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": "perspective-test-commit"},
    )
    assert commit.status_code == 200


def test_perspective_requires_owned_committed_session() -> None:
    client = TestClient(create_app())
    owner_headers = _guest(client)
    other_headers = _guest(client)
    session_id = _start(client, owner_headers)

    before_commit = client.get(
        f"/v1/weigh-sessions/{session_id}/perspectives",
        headers=owner_headers,
    )
    assert before_commit.status_code == 403
    assert before_commit.json()["code"] == "RESULT_COMMIT_REQUIRED"

    foreign = client.get(
        f"/v1/weigh-sessions/{session_id}/perspectives",
        headers=other_headers,
    )
    assert foreign.status_code == 404
    assert foreign.json()["code"] == "WEIGH_SESSION_NOT_FOUND"


def test_perspective_returns_bounded_curated_cards_after_commit() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    session_id = _start(client, headers)
    _commit(client, session_id, headers)

    response = client.get(
        f"/v1/weigh-sessions/{session_id}/perspectives",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["methodology"]["mode"] == "DEGRADED_CURATED"
    assert body["methodology"]["sample_kind"] == "CURATED_FALLBACK"
    assert body["methodology"]["sample_size"] == 4
    assert [card["slot"] for card in body["cards"]] == [
        "NEAR",
        "OPPOSING",
        "BRIDGE",
        "ALTERNATIVE_CONTEXT",
    ]
    assert all(card["source_kind"] == "CURATED" for card in body["cards"])
    assert all(card["moderation_state"] == "NOT_REQUIRED" for card in body["cards"])


def test_private_reason_never_leaks_into_perspective_or_event() -> None:
    app = create_app()
    client = TestClient(app)
    headers = _guest(client)
    session_id = _start(client, headers)
    private_text = "yalnız bana ait hassas gerekçe"

    saved = client.put(
        f"/v1/weigh-sessions/{session_id}/reason",
        headers=headers,
        json={"tags": ["FAIRNESS"], "text": private_text},
    )
    assert saved.status_code == 200
    _commit(client, session_id, headers)

    response = client.get(
        f"/v1/weigh-sessions/{session_id}/perspectives",
        headers=headers,
    )

    assert response.status_code == 200
    assert private_text not in response.text
    viewed = [
        event
        for event in app.state.decision_repository.events
        if event["name"] == "perspective.viewed"
    ]
    assert len(viewed) == 1
    assert viewed[0]["payload"] == {
        "case_version_id": response.json()["case_version_id"],
        "mode": "DEGRADED_CURATED",
        "card_count": 4,
    }
    assert private_text not in str(viewed[0])
