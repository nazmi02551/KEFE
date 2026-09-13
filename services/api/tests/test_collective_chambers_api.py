from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_consensus_circle_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res_get = client.get(f"/v1/cases/{case_id}/consensus-circle")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["capability_id"] == "CAP-086"
    assert data_get["state"] == "SYNTHESIS_PACT_RATIFIED"

    payload = {
        "circle_id": "crc-custom-01",
        "pact_title": "Kentsel Tarım ve İmar Planı Sözleşmesi",
        "stakeholder_groups_count": 3,
        "mutual_concession_score": 0.65,
        "synthesis_covenant_summary": "Tarım arazilerinin korunması ve kontrollü yerleşim dengesi.",
    }
    res_post = client.post(f"/v1/cases/{case_id}/consensus-circle", json=payload)
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["circle_id"] == "crc-custom-01"
    assert data_post["state"] == "INTERMEDIATE_CONCESSION_BARGAINING"
    assert data_post["mutual_concession_score"] == 0.65


def test_boardroom_deliberation_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res_get = client.get(f"/v1/cases/{case_id}/boardroom")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["capability_id"] == "CAP-087"
    assert data_get["dilemma_scope"] == "ESG_AND_SUSTAINABILITY"
    assert data_get["fiduciary_consensus_ratio"] == 0.78

    payload = {
        "room_id": "room-custom-02",
        "organization_name": "Avrupa İklim Girişimi Vakfı",
        "dilemma_scope": "CRISIS_MANAGEMENT",
        "board_member_count": 12,
        "votes_in_favor": 10,
        "esg_alignment_score": 0.88,
    }
    res_post = client.post(f"/v1/cases/{case_id}/boardroom", json=payload)
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["dilemma_scope"] == "CRISIS_MANAGEMENT"
    assert data_post["fiduciary_consensus_ratio"] == 0.83


def test_youth_deliberation_space_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res_get = client.get(f"/v1/cases/{case_id}/youth-space")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["capability_id"] == "CAP-088"
    assert data_get["focus_area"] == "CAMPUS_AND_EDUCATION_POLICY"
    assert data_get["active_student_count"] == 420

    payload = {
        "space_id": "youth-custom-03",
        "space_name": "İTÜ Öğrenci İklim İnisiyatifi",
        "focus_area": "CLIMATE_AND_INTERGENERATIONAL",
        "institution_or_community": "İstanbul Teknik Üniversitesi",
        "active_student_count": 580,
        "consensus_action_count": 8,
    }
    res_post = client.post(f"/v1/cases/{case_id}/youth-space", json=payload)
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["focus_area"] == "CLIMATE_AND_INTERGENERATIONAL"
    assert data_post["active_student_count"] == 580


def test_citizen_jury_chamber_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res_get = client.get(f"/v1/cases/{case_id}/citizen-jury")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["reference_adr"] == "ADR-0223"
    assert data_get["stage"] == "CONSENSUS_VERDICT_EMITTED"
    assert data_get["juror_count"] == 24

    payload = {
        "jury_id": "jury-custom-04",
        "dilemma_title": "Yenilenebilir Enerji Santrali Yer Seçimi",
        "stage": "EXPERT_HEARINGS_IN_SESSION",
        "juror_count": 30,
        "expert_witnesses_count": 6,
        "verdict_consensus_rate": 0.75,
    }
    res_post = client.post(f"/v1/cases/{case_id}/citizen-jury", json=payload)
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["stage"] == "EXPERT_HEARINGS_IN_SESSION"
    assert data_post["verdict_consensus_rate"] == 0.75
