from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_academic_research_portal_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res_get = client.get(f"/v1/cases/{case_id}/academic-research")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["capability_id"] == "CAP-109"
    assert data_get["reference_adr"] == "ADR-0209"
    assert data_get["contract_id"] == "KEFE-ACAD-PORTAL-001"
    assert data_get["corpus_type"] == "DELIBERATIVE_POLARIZATION_DATASET"
    assert data_get["record_count"] == 1250
    assert data_get["differential_privacy_epsilon"] == 0.15
    assert data_get["doi_identifier"] == "doi:10.1000/182"

    payload = {
        "dataset_id": "data-custom-01",
        "dataset_title": "Tüketici Hakları Etik İkilem Karşılaştırma Veri Seti",
        "corpus_type": "ETHICAL_TRADE_OFF_CORPUS",
        "record_count": 3400,
        "differential_privacy_epsilon": 0.25,
        "doi_identifier": "doi:10.1000/18249",
    }
    res_post = client.post(f"/v1/cases/{case_id}/academic-research", json=payload)
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["dataset_id"] == "data-custom-01"
    assert data_post["corpus_type"] == "ETHICAL_TRADE_OFF_CORPUS"
    assert data_post["record_count"] == 3400
    assert data_post["differential_privacy_epsilon"] == 0.25


def test_ngo_impact_desk_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res_get = client.get(f"/v1/cases/{case_id}/ngo-impact")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["capability_id"] == "CAP-108"
    assert data_get["reference_adr"] == "ADR-0210"
    assert data_get["contract_id"] == "KEFE-NGO-DESK-001"
    assert data_get["advocacy_domain"] == "ENVIRONMENT_AND_CLIMATE"
    assert data_get["citizen_endorsement_count"] == 450
    assert data_get["institutional_reforms_achieved"] == 2
    assert 0.0 <= data_get["advocacy_efficacy_score"] <= 1.0

    payload = {
        "campaign_id": "ngo-custom-02",
        "ngo_name": "Şeffaf Yönetim Derneği",
        "advocacy_domain": "TRANSPARENCY_AND_ANTI_CORRUPTION",
        "citizen_endorsement_count": 800,
        "institutional_reforms_achieved": 3,
    }
    res_post = client.post(f"/v1/cases/{case_id}/ngo-impact", json=payload)
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["campaign_id"] == "ngo-custom-02"
    assert data_post["advocacy_domain"] == "TRANSPARENCY_AND_ANTI_CORRUPTION"
    assert data_post["citizen_endorsement_count"] == 800
    assert data_post["institutional_reforms_achieved"] == 3
    assert data_post["advocacy_efficacy_score"] == 0.85


def test_civic_petition_simulator_api() -> None:
    app = create_app()
    client = TestClient(app)

    case_id = str(uuid4())
    res_get = client.get(f"/v1/cases/{case_id}/civic-petition")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["reference_adr"] == "ADR-0225"
    assert data_get["contract_id"] == "KEFE-PETITION-SIM-001"
    assert data_get["stage"] == "SIGNATURE_GATHERING_CAMPAIGN"
    assert data_get["signatures_count"] == 1500
    assert data_get["signature_target_threshold"] == 2000
    assert data_get["projected_net_benefit_score"] == 0.42

    payload = {
        "petition_id": "pet-custom-03",
        "bill_title": "Temiz Enerji ve Karbon Salımı Sınırlama Kanunu",
        "signatures_count": 5500,
        "signature_target_threshold": 5000,
        "projected_net_benefit_score": 0.68,
    }
    res_post = client.post(f"/v1/cases/{case_id}/civic-petition", json=payload)
    assert res_post.status_code == 200
    data_post = res_post.json()
    assert data_post["petition_id"] == "pet-custom-03"
    assert data_post["stage"] == "SUBMITTED_TO_PARLIAMENT"
    assert data_post["signatures_count"] == 5500
    assert data_post["signature_target_threshold"] == 5000
    assert data_post["projected_net_benefit_score"] == 0.68
