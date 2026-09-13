from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_wave5_advanced_synthesis_divergence_api() -> None:
    app = create_app()
    client = TestClient(app)
    case_id = uuid4()

    # 1. CAP-007: Role Flip
    res_rf = client.get(f"/v1/cases/{case_id}/role-flip")
    assert res_rf.status_code == 200
    data_rf = res_rf.json()
    assert data_rf["capability_id"] == "CAP-007"
    assert data_rf["initial_role"] == "Tesis Sahibi / Sanayici"
    assert data_rf["flipped_role"] == "Bölge Sakini / Temiz Su Tüketicisi"
    assert data_rf["perspective_shift_score"] == 0.74

    # 2. CAP-010: Change Mind Inquiry
    res_cm = client.get(f"/v1/cases/{case_id}/change-mind-inquiry")
    assert res_cm.status_code == 200
    data_cm = res_cm.json()
    assert data_cm["capability_id"] == "CAP-010"
    assert data_cm["flexibility_class"] == "HIGHLY_EPISTEMIC_OPEN"
    assert len(data_cm["selected_conditions"]) == 2

    # 3. CAP-034: Bridge Arguments
    res_ba = client.get(f"/v1/cases/{case_id}/bridge-arguments")
    assert res_ba.status_code == 200
    data_ba = res_ba.json()
    assert isinstance(data_ba, list)
    assert len(data_ba) >= 1
    assert data_ba[0]["capability_id"] == "CAP-034"
    assert data_ba[0]["cross_group_support_rate"] == 0.62
    assert data_ba[0]["sample_size"] >= 30

    # 4. CAP-038: Stakeholder Gap
    res_sg = client.get(f"/v1/cases/{case_id}/stakeholder-gap?segment_key=DIRECTLY_AFFECTED&target_option=A")
    assert res_sg.status_code == 200
    data_sg = res_sg.json()
    assert data_sg["capability_id"] == "CAP-038"
    assert data_sg["segment_key"] == "DIRECTLY_AFFECTED"
    assert data_sg["target_option"] == "A"
    assert data_sg["gap_points"] == 16
    assert data_sg["k_anonymity_satisfied"] is True

    # 5. CAP-040: Divergence Anatomy
    res_da = client.get(f"/v1/cases/{case_id}/divergence-anatomy")
    assert res_da.status_code == 200
    data_da = res_da.json()
    assert data_da["capability_id"] == "CAP-040"
    assert data_da["primary_driver"] == "NORMATIVE_VALUE_WEIGHT"
    assert len(data_da["drivers"]) == 3
    assert sum(d["share_percentage"] for d in data_da["drivers"]) == 100.0
