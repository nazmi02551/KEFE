from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_budget_tradeoff_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = "22222222-2222-4222-8222-222222222222"

    # 1. GET default budget tradeoff
    res = client.get(f"/v1/cases/{case_id}/budget-tradeoff")
    assert res.status_code == 200
    data = res.json()
    assert data["case_version_id"] == case_id
    assert data["healthcare_pct"] == 30
    assert data["education_pct"] == 25
    assert data["tradeoff_profile"] == "HEALTH_EDUCATION_PRIORITY"

    # 2. POST evaluate valid tradeoff
    eval_res = client.post(
        f"/v1/cases/{case_id}/budget-tradeoff/evaluate",
        json={
            "healthcare_pct": 20,
            "education_pct": 20,
            "infrastructure_pct": 45,
            "green_transition_pct": 15,
        },
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["infrastructure_pct"] == 45
    assert eval_data["tradeoff_profile"] == "INFRASTRUCTURE_GROWTH"

    # 3. POST evaluate invalid tradeoff (> 100%)
    invalid_res = client.post(
        f"/v1/cases/{case_id}/budget-tradeoff/evaluate",
        json={
            "healthcare_pct": 50,
            "education_pct": 50,
            "infrastructure_pct": 50,
            "green_transition_pct": 50,
        },
    )
    assert invalid_res.status_code == 400
    assert "cannot exceed 100%" in invalid_res.json()["detail"]


def test_historical_retrospective_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = "22222222-2222-4222-8222-222222222222"
    res = client.get(f"/v1/cases/{case_id}/historical-retrospective")
    assert res.status_code == 200
    data = res.json()
    assert data["case_version_id"] == case_id
    assert data["historical_era"] == "INDUSTRIAL_ERA"
    assert data["historical_year"] == 1888
    assert "Demiryolu" in data["historical_event_name"]
    assert "kamu mülkiyeti" in data["actual_historical_decision"]


def test_observe_session_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = "22222222-2222-4222-8222-222222222222"

    # Default mode
    res = client.post(f"/v1/cases/{case_id}/observe-session")
    assert res.status_code == 200
    data = res.json()
    assert data["case_version_id"] == case_id
    assert data["exploration_mode"] == "OBSERVE_ONLY"
    assert data["is_binding_vote"] is False

    # Custom mode
    res_study = client.post(
        f"/v1/cases/{case_id}/observe-session",
        json={"exploration_mode": "STUDY_AND_LEARN"},
    )
    assert res_study.status_code == 200
    data_study = res_study.json()
    assert data_study["exploration_mode"] == "STUDY_AND_LEARN"
    assert data_study["is_binding_vote"] is False


def test_community_proposals_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = "22222222-2222-4222-8222-222222222222"

    # 1. GET pre-seeded list
    res = client.get(f"/v1/cases/{case_id}/community-proposals")
    assert res.status_code == 200
    proposals = res.json()
    assert isinstance(proposals, list)
    assert len(proposals) >= 1

    # 2. POST create proposal
    post_res = client.post(
        f"/v1/cases/{case_id}/community-proposals",
        json={
            "proposed_title": "Tarihi Çarşı Bölgesi Yaya Bölgesi İlan Edilsin",
            "proposed_context": "Esnafın yük teslimat saatleri düzenlenerek motorlu taşıt trafiğine tamamen kapatılması önerilmektedir.",
        },
    )
    assert post_res.status_code == 201
    created = post_res.json()
    assert created["curation_state"] == "DRAFT_SUBMITTED"
    assert "Tarihi Çarşı" in created["proposed_title"]

    # 3. GET verify newly added shows up
    res_after = client.get(f"/v1/cases/{case_id}/community-proposals")
    assert res_after.status_code == 200
    assert len(res_after.json()) >= 2
