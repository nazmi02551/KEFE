from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_list_institution_responses_endpoint() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.get("/v1/impact/institution-responses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    first = data[0]
    assert "response_id" in first
    assert "case_version_id" in first
    assert "institution_name" in first
    assert "statement" in first
    assert first["verification_status"] == "VERIFIED"
    assert first["response_type"] in [
        "POLICY_CHANGE",
        "COMMITMENT",
        "ACKNOWLEDGE",
    ]


def test_filter_institution_responses_by_case() -> None:
    app = create_app()
    client = TestClient(app)

    target_case = "22222222-2222-4222-8222-222222222222"
    response = client.get(
        f"/v1/impact/institution-responses?case_version_id={target_case}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for item in data:
        assert item["case_version_id"] == target_case
