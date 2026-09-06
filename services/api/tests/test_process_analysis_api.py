from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.decision.process_analysis import (
    ProcessStageEnum,
    PublicParticipationStatus,
    TransparencyLevel,
)


def test_process_analysis_api_get() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res = client.get(f"/v1/cases/{case_id}/process-analysis")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == case_id
    assert data["analysis_id"].startswith("PROC-")
    assert data["current_stage"] in [e.value for e in ProcessStageEnum]
    assert 0.0 <= data["procedural_integrity_score"] <= 1.0
    assert data["transparency_level"] in [e.value for e in TransparencyLevel]
    assert data["public_participation_status"] in [e.value for e in PublicParticipationStatus]
    assert len(data["oversight_body"]) >= 3
    assert len(data["stages"]) >= 3

    for stage in data["stages"]:
        assert "stage_key" in stage
        assert "stage_title" in stage
        assert isinstance(stage["is_completed"], bool)
        assert isinstance(stage["duration_days"], int)
        assert isinstance(stage["has_public_input"], bool)
