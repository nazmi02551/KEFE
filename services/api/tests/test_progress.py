from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_QUESTION_ID


def _guest(client: TestClient) -> dict[str, str]:
    response = client.post("/v1/identity/guest")
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _commit_demo(client: TestClient, headers: dict[str, str]) -> None:
    started = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
        headers=headers,
    )
    assert started.status_code == 201
    session_id = started.json()["session_id"]
    answered = client.put(
        f"/v1/weigh-sessions/{session_id}/responses",
        headers=headers,
        json={
            "responses": [
                {"question_id": str(DEMO_QUESTION_ID), "value": "A"},
            ]
        },
    )
    assert answered.status_code == 200
    committed = client.post(
        f"/v1/weigh-sessions/{session_id}/commit",
        headers={**headers, "Idempotency-Key": "progress-demo-0001"},
    )
    assert committed.status_code == 200


def test_progress_requires_authentication() -> None:
    client = TestClient(create_app())
    response = client.get("/v1/me/progress")
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_REQUIRED"


def test_empty_progress_is_low_claim_and_guest_safe() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    response = client.get("/v1/me/progress", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["account_offer"] == {
        "eligible": False,
        "placement": "POST_REVEAL",
        "blocking": False,
        "dismissible": True,
        "continue_as_guest_available": True,
        "account_creation_available": False,
    }
    assert body["progress"]["readiness"] == "INSUFFICIENT_DATA"
    assert body["progress"]["meaningful_weigh_count"] == 0
    assert body["progress"]["recent_cases"] == []
    assert body["journey"] == {
        "decision_update_count": 0,
        "revisited_case_count": 0,
        "reflection_completion_count": 0,
        "domain_activity": [],
        "recent_journeys": [],
    }
    serialized = response.text.lower()
    for forbidden in (
        "token",
        "private_reason",
        "raw_response",
        "personality",
        "ideology",
        "psychometric",
        "streak",
        "xp",
        "exposure_metadata",
        "intervention_metadata",
    ):
        assert forbidden not in serialized


def test_committed_decision_unlocks_offer_and_descriptive_journey() -> None:
    client = TestClient(create_app())
    headers = _guest(client)
    _commit_demo(client, headers)

    response = client.get("/v1/me/progress", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["account_offer"]["eligible"] is True
    assert body["account_offer"]["account_creation_available"] is False
    assert body["progress"]["meaningful_weigh_count"] == 1
    assert body["progress"]["distinct_case_count"] == 1
    assert body["progress"]["distinct_domain_count"] == 1
    assert body["progress"]["readiness"] == "INSUFFICIENT_DATA"
    assert len(body["progress"]["recent_cases"]) == 1
    recent = body["progress"]["recent_cases"][0]
    assert recent["case_id"] == str(DEMO_CASE_ID)
    assert recent["primary_domain"] == "DAILY_LIFE"

    journey = body["journey"]
    assert journey["decision_update_count"] == 0
    assert journey["revisited_case_count"] == 0
    assert journey["reflection_completion_count"] == 0
    assert journey["domain_activity"] == [
        {
            "primary_domain": "DAILY_LIFE",
            "committed_weigh_count": 1,
            "last_committed_at": recent["committed_at"],
        }
    ]
    assert len(journey["recent_journeys"]) == 1
    item = journey["recent_journeys"][0]
    assert item["case_id"] == str(DEMO_CASE_ID)
    assert item["primary_domain"] == "DAILY_LIFE"
    assert item["decision_update_count"] == 0
    assert item["reflection_completed"] is False
    assert item["initial_committed_at"] == recent["committed_at"]
    assert item["latest_decision_at"] == recent["committed_at"]
    assert body["methodology"]["journey_semantics"] == "OBSERVED_PRODUCT_HISTORY_ONLY"
    assert body["methodology"]["causal_claims"] == "NONE"
