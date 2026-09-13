from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app

client = TestClient(create_app())


def test_inspect_cluster_quarantine_swarm() -> None:
    response = client.post(
        "/v1/trust/shield/inspect",
        json={
            "cluster_id": "test_swarm_001",
            "target_case_id": "case_101",
            "synthetic_probability_score": 0.95,
            "quarantined_bot_payloads_count": 500,
            "semantic_entropy_index": 0.15,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cluster_id"] == "test_swarm_001"
    assert data["target_case_id"] == "case_101"
    assert data["defense_state"] == "ISOLATED_QUARANTINE_SWARM"
    assert data["synthetic_probability_score"] == 0.95
    assert data["quarantined_bot_payloads_count"] == 500
    assert data["semantic_entropy_index"] == 0.15
    assert data["is_quarantined"] is True
    assert "inspected_at" in data


def test_inspect_cluster_suspected_coordination() -> None:
    response = client.post(
        "/v1/trust/shield/inspect",
        json={
            "cluster_id": "test_susp_002",
            "target_case_id": "case_102",
            "synthetic_probability_score": 0.60,
            "quarantined_bot_payloads_count": 50,
            "semantic_entropy_index": 0.45,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["defense_state"] == "SUSPECTED_BOT_COORDINATION"
    assert data["is_quarantined"] is False


def test_inspect_cluster_organic_authentic() -> None:
    response = client.post(
        "/v1/trust/shield/inspect",
        json={
            "cluster_id": "test_org_003",
            "target_case_id": "case_103",
            "synthetic_probability_score": 0.12,
            "quarantined_bot_payloads_count": 0,
            "semantic_entropy_index": 0.85,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["defense_state"] == "ORGANIC_CITIZEN_AUTHENTIC"
    assert data["is_quarantined"] is False


def test_inspect_cluster_validation_error() -> None:
    response = client.post(
        "/v1/trust/shield/inspect",
        json={
            "cluster_id": "x",  # min_length is 2
            "target_case_id": "case_104",
            "synthetic_probability_score": 1.5,  # out of bounds
            "quarantined_bot_payloads_count": -5,  # negative
            "semantic_entropy_index": 0.5,
        },
    )
    assert response.status_code == 422


def test_agenda_thresholding_evaluation() -> None:
    response = client.post(
        "/v1/trust/agenda/evaluate",
        json={
            "topic_id": "topic_water_crisis",
            "topic_title": "Water Crisis & Infrastructure",
            "resonance_velocity_index": 0.88,
            "viewpoint_diversity_entropy": 0.76,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["topic_id"] == "topic_water_crisis"
    assert data["topic_title"] == "Water Crisis & Infrastructure"
    assert data["priority_tier"] == "NATIONAL_URGENCY_SPIKE"
    assert data["is_featured_on_national_ballot"] is True
    assert "evaluated_at" in data


def test_agenda_thresholding_incubation() -> None:
    response = client.post(
        "/v1/trust/agenda/evaluate",
        json={
            "topic_id": "topic_local_transit",
            "topic_title": "Local Transit Micro-Routing",
            "resonance_velocity_index": 0.20,
            "viewpoint_diversity_entropy": 0.30,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["priority_tier"] == "MONITORED_INCUBATION"
    assert data["is_featured_on_national_ballot"] is False


def test_list_and_update_clusters() -> None:
    response = client.get("/v1/trust/clusters")
    assert response.status_code == 200
    clusters = response.json()
    assert len(clusters) >= 2
    cluster_ids = [c["cluster_id"] for c in clusters]
    assert "bot_cls_001" in cluster_ids

    # Update status of bot_cls_001 to RESOLVED
    update_res = client.post(
        "/v1/trust/clusters/bot_cls_001/status?new_status=RESOLVED"
    )
    assert update_res.status_code == 200
    assert update_res.json()["quarantine_status"] == "RESOLVED"
