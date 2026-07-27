from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.context.bootstrap import (
    DEMO_CONTEXT_BLOCK_ID,
    DEMO_CONTEXT_DETAIL_ID,
    DEMO_CONTEXT_SOURCE_ID,
)
from kefe_api.modules.decision.bootstrap import DEMO_CASE_VERSION_ID


def test_context_is_public_case_version_pinned_and_result_free() -> None:
    client = TestClient(create_app())
    response = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")

    assert response.status_code == 200
    body = response.json()
    assert body["case_version_id"] == str(DEMO_CASE_VERSION_ID)
    assert [item["context_block_id"] for item in body["blocks"]] == [
        str(DEMO_CONTEXT_BLOCK_ID),
        str(DEMO_CONTEXT_DETAIL_ID),
    ]
    assert body["blocks"][0]["disclosure_level"] == "ESSENTIAL"
    assert body["blocks"][0]["claim_status"] == "VERIFIED"
    assert body["sources"][0]["source_id"] == str(DEMO_CONTEXT_SOURCE_ID)

    serialized = response.text
    for forbidden in ("result", "perspective", "participant_reason", "community"):
        assert forbidden not in serialized.lower()


def test_unknown_case_version_context_returns_stable_error() -> None:
    client = TestClient(create_app())
    response = client.get(
        "/v1/case-versions/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/context"
    )

    assert response.status_code == 404
    assert response.json()["code"] == "CASE_VERSION_CONTEXT_NOT_FOUND"
