from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_get_blind_variants_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    res = client.get(f"/v1/cases/{case_version_id}/blind-variants")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == str(case_version_id)
    assert data["capability_id"] == "CAP-005"
    assert data["blind_mode"] == "ACTOR_BLIND"
    assert len(data["blinded_prompt"]) >= 10
    assert len(data["real_identity_revealed"]) >= 5
    assert 0.0 <= data["neutrality_score"] <= 1.0


def test_get_principle_first_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    res = client.get(f"/v1/cases/{case_version_id}/principle-first")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == str(case_version_id)
    assert data["capability_id"] == "CAP-006"
    assert data["primary_principle"] == "COLLECTIVE_WELLBEING"
    assert data["secondary_principle"] == "PROCEDURAL_JUSTICE"
    assert data["consistency_score"] >= 0.0
    assert len(data["reflection_prompt"]) >= 5


def test_get_decision_receipt_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    res = client.get(f"/v1/cases/{case_version_id}/decision-receipt")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == str(case_version_id)
    assert data["capability_id"] == "CAP-012"
    assert data["committed_choice"] == "OPTION_A"
    assert len(data["integrity_digest"]) == 64
    assert data["receipt_id"].startswith("kefe-rcpt-")


def test_get_outcome_triangle_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    res = client.get(f"/v1/cases/{case_version_id}/outcome-triangle")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == str(case_version_id)
    assert data["capability_id"] == "CAP-102"
    assert data["option_code"] == "OPTION_A"
    assert abs(data["rules_weight"] + data["empathy_weight"] + data["utility_weight"] - 1.0) < 0.01
    assert data["dominant_archetype"] in (
        "RIGHTS_CENTRIC",
        "EMPATHY_CENTRIC",
        "UTILITY_CENTRIC",
        "TRI_BALANCED_HARMONY",
    )


def test_get_insufficient_info_report_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    res = client.get(f"/v1/cases/{case_version_id}/insufficient-info-report")
    assert res.status_code == 200
    data = res.json()

    assert data["case_version_id"] == str(case_version_id)
    assert "CAP-011" in data["capabilities"]
    assert data["total_opt_outs"] == 48
    assert len(data["breakdown"]) == 2
    assert data["preserves_commit_first_isolation"] is True
