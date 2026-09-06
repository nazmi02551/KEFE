from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.responsibility_analysis import DutyNatureEnum


def test_responsibility_analysis_api_get() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_id}/responsibility-analysis")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert data["analysis_id"].startswith("RESP-")
    assert 0.0 <= data["clarity_score"] <= 1.0
    assert isinstance(data["has_accountability_gap"], bool)
    assert len(data["legal_redress_channel"]) >= 3
    assert len(data["actor_allocations"]) >= 3

    valid_duties = [d.value for d in DutyNatureEnum]
    for alloc in data["actor_allocations"]:
        assert "actor_key" in alloc
        assert "actor_name" in alloc
        assert 0.0 <= alloc["responsibility_share"] <= 1.0
        assert alloc["duty_nature"] in valid_duties
        assert len(alloc["jurisdiction_scope"]) > 0
