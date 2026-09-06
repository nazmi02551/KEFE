from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_list_and_submit_case_objections_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = "22222222-2222-4222-8222-222222222222"

    # 1. List pre-seeded objections
    res = client.get(f"/v1/cases/{case_version_id}/objections")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["case_version_id"] == case_version_id
    assert data[0]["reason_category"] == "EDITORIAL_BIAS_FRAMING"
    assert data[0]["status"] == "SUBMITTED"

    # 2. Submit new objection
    submit_res = client.post(
        f"/v1/cases/{case_version_id}/objections",
        json={
            "reason_category": "EXCLUDED_STAKEHOLDER",
            "statement": "Engelli ve hareket kısıtlılığı olan yolcuların bakış açısı bu ikilemde yeterince temsil edilmemiş.",
            "supporting_evidence_url": "https://kefe.org/delil/engelli-haklari",
        },
    )
    assert submit_res.status_code == 201
    created = submit_res.json()
    assert "objection_id" in created
    assert created["reason_category"] == "EXCLUDED_STAKEHOLDER"
    assert created["status"] == "SUBMITTED"
    assert (
        created["supporting_evidence_url"]
        == "https://kefe.org/delil/engelli-haklari"
    )

    # 3. Verify it shows in list
    res_after = client.get(f"/v1/cases/{case_version_id}/objections")
    assert res_after.status_code == 200
    assert len(res_after.json()) >= 2
