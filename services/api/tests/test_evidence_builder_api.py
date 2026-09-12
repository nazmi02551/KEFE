from __future__ import annotations

from uuid import uuid4
from fastapi.testclient import TestClient

from kefe_api.main import create_app


def test_create_and_list_evidence() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    payload = {
        "case_version_id": str(case_version_id),
        "category": "ACADEMIC_PEER_REVIEWED",
        "title": "Study on Civic Deliberation Resilience",
        "publisher": "Oxford Academic",
        "source_url": "https://academic.example.com/civic-study",
        "doi_or_doc_ref": "doi:10.1093/oxford/civic101",
    }

    create_res = client.post("/v1/evidence", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["title"] == payload["title"]
    assert created["verification_status"] == "UNVERIFIED"
    assert created["contract_id"] == "KEFE-EVIDENCE-BUILDER-001"

    evidence_id = created["evidence_id"]

    # List evidence for case
    list_res = client.get(f"/v1/evidence/case/{case_version_id}")
    assert list_res.status_code == 200
    evidence_list = list_res.json()
    assert any(e["evidence_id"] == evidence_id for e in evidence_list)


def test_verify_evidence_status_advance() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    payload = {
        "case_version_id": str(case_version_id),
        "category": "OFFICIAL_GOVERNMENT_STAT",
        "title": "National Census Statistics on Deliberation Engagement",
        "publisher": "State Statistics Institute",
        "doi_or_doc_ref": "doc-ref-stat-2026-09",
    }
    create_res = client.post("/v1/evidence", json=payload)
    evidence_id = create_res.json()["evidence_id"]

    verify_payload = {
        "new_status": "EXPERT_AUDITED",
        "auditor_id": "auditor-expert-42",
        "audit_notes": "Verified against state statistics gazette.",
    }
    verify_res = client.post(f"/v1/evidence/{evidence_id}/verify", json=verify_payload)
    assert verify_res.status_code == 200
    updated = verify_res.json()
    assert updated["verification_status"] == "EXPERT_AUDITED"


def test_create_evidence_missing_verifiable_ref_fails() -> None:
    app = create_app()
    client = TestClient(app)

    case_version_id = uuid4()
    payload = {
        "case_version_id": str(case_version_id),
        "category": "INVESTIGATIVE_JOURNALISM",
        "title": "Investigation Without References",
        "publisher": "Unknown Journal",
    }
    res = client.post("/v1/evidence", json=payload)
    assert res.status_code == 400
    assert "Either source_url or doi_or_doc_ref must be provided" in res.json()["detail"]
