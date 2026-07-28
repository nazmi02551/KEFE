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
    serialized = response.text.lower()
    for forbidden in ("token", "private_reason", "personality", "ideology", "streak", "xp"):
        assert forbidden not in serialized


def test_committed_decision_unlocks_optional_offer_and_progress() -> None:
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
