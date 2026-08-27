from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_guest_renewal_http_preserves_actor_and_converges_retry() -> None:
    client = TestClient(create_app())

    issued = client.post(
        "/v1/identity/guest",
        json={"platform": "ANDROID"},
    )
    assert issued.status_code == 201
    initial = issued.json()
    assert initial["actor_kind"] == "GUEST"
    assert initial["rotation_counter"] == 0
    assert initial["renewal_token"].startswith("kefe_r_")

    renewed = client.post(
        "/v1/identity/session/renew",
        json={"renewal_token": initial["renewal_token"]},
    )
    assert renewed.status_code == 200
    current = renewed.json()
    assert current["actor_id"] == initial["actor_id"]
    assert current["actor_kind"] == "GUEST"
    assert current["rotation_counter"] == 1
    assert current["access_token"] != initial["access_token"]
    assert current["renewal_token"] != initial["renewal_token"]

    retry = client.post(
        "/v1/identity/session/renew",
        json={"renewal_token": initial["renewal_token"]},
    )
    assert retry.status_code == 200
    retried = retry.json()
    assert retried["actor_id"] == current["actor_id"]
    assert retried["rotation_counter"] == current["rotation_counter"]
    assert retried["access_token"] == current["access_token"]
    assert retried["renewal_token"] == current["renewal_token"]
