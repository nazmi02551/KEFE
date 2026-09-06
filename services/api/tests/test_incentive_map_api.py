from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.incentive_map import (
    AlignmentStatusEnum,
    IncentiveTypeEnum,
    PerverseRiskEnum,
)


def test_incentive_map_api_get() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_id}/incentive-map")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert data["map_id"].startswith("INC-")
    assert 0.0 <= data["alignment_index"] <= 1.0
    assert data["perverse_incentive_risk"] in [e.value for e in PerverseRiskEnum]
    assert len(data["primary_driver"]) >= 3
    assert len(data["mitigation_mechanism"]) >= 3
    assert len(data["incentive_nodes"]) >= 3

    valid_types = [t.value for t in IncentiveTypeEnum]
    valid_statuses = [s.value for s in AlignmentStatusEnum]

    for node in data["incentive_nodes"]:
        assert len(node["stakeholder_group"]) > 0
        assert len(node["core_incentive"]) > 0
        assert node["incentive_type"] in valid_types
        assert node["alignment_status"] in valid_statuses
        assert 0.0 <= node["intensity_score"] <= 1.0
