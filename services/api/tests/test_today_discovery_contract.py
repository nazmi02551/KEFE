from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_explore_summary_exposes_backward_safe_real_event_marker() -> None:
    response = TestClient(create_app()).get("/v1/cases?limit=1")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["is_real_event"] is False
    assert "questions" not in item
    assert "result" not in item
