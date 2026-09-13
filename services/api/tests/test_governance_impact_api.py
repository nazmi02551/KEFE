from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.process_analysis import (
    ProcessStageEnum,
    PublicParticipationStatus,
    TransparencyLevel,
)
from kefe_api.modules.decision.responsibility_analysis import DutyNatureEnum
from kefe_api.modules.decision.incentive_map import (
    AlignmentStatusEnum,
    IncentiveTypeEnum,
    PerverseRiskEnum,
)
from kefe_api.modules.decision.stakeholder_impact import (
    StakeholderGroupType,
    StakeholderImpactType,
)


def test_wave_6_governance_impact_suite_api() -> None:
    app = create_app()
    client = TestClient(app)
    case_id = str(uuid4())

    # 1. CAP-018: Threshold Sensitivity Analysis
    res_thresh = client.get(f"/v1/cases/{case_id}/threshold-analysis")
    assert res_thresh.status_code == 200, res_thresh.text
    data_thresh = res_thresh.json()
    assert data_thresh["case_version_id"] == case_id
    assert "parameter_name" in data_thresh
    assert data_thresh["unit"] == "TL"
    assert data_thresh["tipping_point_threshold"] == 20.0
    assert len(data_thresh["curve_points"]) == 4
    for pt in data_thresh["curve_points"]:
        assert "parameter_value" in pt
        assert 0.0 <= pt["acceptance_rate"] <= 1.0

    # 2. CAP-020: Responsibility Analysis
    res_resp = client.get(f"/v1/cases/{case_id}/responsibility-analysis")
    assert res_resp.status_code == 200, res_resp.text
    data_resp = res_resp.json()
    assert data_resp["case_version_id"] == case_id
    assert data_resp["analysis_id"].startswith("RESP-")
    assert 0.0 <= data_resp["clarity_score"] <= 1.0
    assert isinstance(data_resp["has_accountability_gap"], bool)
    assert len(data_resp["actor_allocations"]) >= 3
    valid_duties = [d.value for d in DutyNatureEnum]
    for alloc in data_resp["actor_allocations"]:
        assert alloc["duty_nature"] in valid_duties
        assert 0.0 <= alloc["responsibility_share"] <= 1.0

    # 3. CAP-021: Process Analysis
    res_proc = client.get(f"/v1/cases/{case_id}/process-analysis")
    assert res_proc.status_code == 200, res_proc.text
    data_proc = res_proc.json()
    assert data_proc["case_version_id"] == case_id
    assert data_proc["current_stage"] in [e.value for e in ProcessStageEnum]
    assert 0.0 <= data_proc["procedural_integrity_score"] <= 1.0
    assert data_proc["transparency_level"] in [e.value for e in TransparencyLevel]
    assert data_proc["public_participation_status"] in [e.value for e in PublicParticipationStatus]
    assert len(data_proc["stages"]) >= 3

    # 4. CAP-022: Incentive Map
    res_inc = client.get(f"/v1/cases/{case_id}/incentive-map")
    assert res_inc.status_code == 200, res_inc.text
    data_inc = res_inc.json()
    assert data_inc["case_version_id"] == case_id
    assert data_inc["map_id"].startswith("INC-")
    assert 0.0 <= data_inc["alignment_index"] <= 1.0
    assert data_inc["perverse_incentive_risk"] in [e.value for e in PerverseRiskEnum]
    assert len(data_inc["incentive_nodes"]) >= 3
    valid_types = [t.value for t in IncentiveTypeEnum]
    valid_statuses = [s.value for s in AlignmentStatusEnum]
    for node in data_inc["incentive_nodes"]:
        assert node["incentive_type"] in valid_types
        assert node["alignment_status"] in valid_statuses
        assert 0.0 <= node["intensity_score"] <= 1.0

    # 5. CAP-023: Stakeholder Impact Matrix
    res_impact = client.get(f"/v1/cases/{case_id}/stakeholder-impact?option_code=OPTION_A")
    assert res_impact.status_code == 200, res_impact.text
    data_impact = res_impact.json()
    assert data_impact["case_version_id"] == case_id
    assert data_impact["option_code"] == "OPTION_A"
    assert isinstance(data_impact["net_equity_score"], int)
    assert len(data_impact["impact_items"]) == 4
    valid_groups = [g.value for g in StakeholderGroupType]
    valid_impacts = [i.value for i in StakeholderImpactType]
    for item in data_impact["impact_items"]:
        assert item["stakeholder_group"] in valid_groups
        assert item["impact_type"] in valid_impacts
        assert -5 <= item["impact_score"] <= 5
        assert len(item["description"]) > 0
