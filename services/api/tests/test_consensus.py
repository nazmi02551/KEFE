from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.consensus.in_memory import DEMO_CONSENSUS_CARD_ID
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
        headers={**headers, "Idempotency-Key": f"consensus-commit-{session_id}"},
    )
    assert commit.status_code == 200


def test_consensus_requires_owned_committed_session() -> None:
    client = TestClient(create_app())
    owner_headers = _guest(client)
    other_headers = _guest(client)
    session_id = _start(client, owner_headers)

    before_commit = client.get(
        f"/v1/weigh-sessions/{session_id}/consensus-cards",
        headers=owner_headers,
    )
    assert before_commit.status_code == 403
    assert before_commit.json()["code"] == "CONSENSUS_COMMIT_REQUIRED"

    foreign = client.get(
        f"/v1/weigh-sessions/{session_id}/consensus-cards",
        headers=other_headers,
    )
    assert foreign.status_code == 404
    assert foreign.json()["code"] == "WEIGH_SESSION_NOT_FOUND"


def test_consensus_hides_aggregate_until_participation() -> None:
    app = create_app()
    client = TestClient(app)
    headers = _guest(client)
    session_id = _start(client, headers)
    _commit(client, session_id, headers)

    response = client.get(
        f"/v1/weigh-sessions/{session_id}/consensus-cards",
        headers=headers,
    )

    assert response.status_code == 200
    card = response.json()["items"][0]
    assert card["card_id"] == str(DEMO_CONSENSUS_CARD_ID)
    assert card["participation_state"] == "ELIGIBLE"
    assert card["contribution_class"] == "EXPOSED"
    assert card["aggregate"] is None
    assert card["participation"] is None
    assert not any(
        event["name"] == "consensus.aggregate_viewed"
        for event in app.state.decision_repository.events
    )


def test_consensus_participation_is_exposed_idempotent_and_reveals_aggregate() -> None:
    app = create_app()
    client = TestClient(app)
    headers = _guest(client)
    session_id = _start(client, headers)
    _commit(client, session_id, headers)
    path = (
        f"/v1/weigh-sessions/{session_id}/consensus-cards/"
        f"{DEMO_CONSENSUS_CARD_ID}/participation"
    )
    request = {
        "stance_code": "AGREE",
        "reason_tag_codes": ["NEED", "FAIRNESS"],
    }
    idempotency = "consensus-participation-0001"

    first = client.post(
        path,
        headers={**headers, "Idempotency-Key": idempotency},
        json=request,
    )
    replay = client.post(
        path,
        headers={**headers, "Idempotency-Key": idempotency},
        json=request,
    )

    assert first.status_code == 200
    assert replay.status_code == 200
    assert replay.json() == first.json()
    body = first.json()
    assert body["participation_state"] == "PARTICIPATED"
    assert body["participation"]["contribution_class"] == "EXPOSED"
    assert body["aggregate"]["contribution_class"] == "EXPOSED"
    assert body["aggregate"]["sample_size"] == 1
    assert body["aggregate"]["stance_distribution"] == {
        "AGREE": 1.0,
        "MIXED": 0.0,
        "DISAGREE": 0.0,
    }
    assert body["aggregate"]["reason_pattern_distribution"] == {
        "NEED": 1.0,
        "FAIRNESS": 1.0,
    }
    assert "Signal" in body["aggregate"]["provenance_note"]

    participated = [
        event
        for event in app.state.decision_repository.events
        if event["name"] == "consensus.participated"
    ]
    aggregate_views = [
        event
        for event in app.state.decision_repository.events
        if event["name"] == "consensus.aggregate_viewed"
    ]
    assert len(participated) == 1
    assert participated[0]["payload"]["contribution_class"] == "EXPOSED"
    assert participated[0]["payload"]["stance_code"] == "AGREE"
    assert "proposition" not in participated[0]["payload"]
    assert len(aggregate_views) == 2
    assert all(
        event["payload"]["contribution_class"] == "EXPOSED"
        for event in aggregate_views
    )
    assert all("proposition" not in event["payload"] for event in aggregate_views)


def test_consensus_rejects_invalid_tags_and_second_participation() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    session_id = _start(client, headers)
    _commit(client, session_id, headers)
    path = (
        f"/v1/weigh-sessions/{session_id}/consensus-cards/"
        f"{DEMO_CONSENSUS_CARD_ID}/participation"
    )

    invalid = client.post(
        path,
        headers={**headers, "Idempotency-Key": "consensus-invalid-0001"},
        json={"stance_code": "AGREE", "reason_tag_codes": ["IDEOLOGY"]},
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "CONSENSUS_REASON_TAG_INVALID"

    accepted = client.post(
        path,
        headers={**headers, "Idempotency-Key": "consensus-valid-0001"},
        json={"stance_code": "MIXED", "reason_tag_codes": ["RULES"]},
    )
    assert accepted.status_code == 200

    second = client.post(
        path,
        headers={**headers, "Idempotency-Key": "consensus-valid-0002"},
        json={"stance_code": "DISAGREE", "reason_tag_codes": []},
    )
    assert second.status_code == 409
    assert second.json()["code"] == "CONSENSUS_ALREADY_PARTICIPATED"
