from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.impact.action_models import ActionMilestone, ActionStatus
from kefe_api.modules.impact.in_memory import InMemoryImpactRepository
from kefe_api.modules.impact.models import (
    AuthorityVerificationStatus,
    InstitutionResponse,
    InstitutionResponseType,
)

_CASE_ID = UUID("22222222-2222-4222-8222-222222222222")
_RESP_ID = UUID("88888888-8888-4888-8888-888888888801")
_ACTION_ID = UUID("99999999-9999-4999-8999-999999999901")

_SEED_RESPONSE = InstitutionResponse(
    response_id=_RESP_ID,
    case_version_id=_CASE_ID,
    institution_name="Ulaştırma ve Altyapı Bakanlığı",
    authority_role="Bakanlık Genel Müdürlüğü",
    verification_status=AuthorityVerificationStatus.VERIFIED,
    response_type=InstitutionResponseType.POLICY_CHANGE,
    statement="Öğrenci tarifelerinde sübvansiyon uygulanacaktır.",
    published_at=datetime(2026, 9, 1, 10, 0, 0, tzinfo=UTC),
)

_SEED_ACTION = ActionMilestone(
    action_id=_ACTION_ID,
    case_version_id=_CASE_ID,
    title="Öğrenci İndirimi Yönetmeliği",
    description="Resmi Gazete tebliği için taslak metin.",
    status=ActionStatus.IN_PROGRESS,
    progress_percentage=40,
    institution_response_id=_RESP_ID,
    created_at=datetime(2026, 9, 2, 10, 0, 0, tzinfo=UTC),
)


def _make_app():
    app = create_app()
    repo = InMemoryImpactRepository()
    repo.save_institution_response(_SEED_RESPONSE)
    repo.save_action(_SEED_ACTION)
    app.state.impact_repository = repo
    return app


def test_attach_action_evidence_api() -> None:
    app = _make_app()
    client = TestClient(app)

    res = client.post(
        f"/v1/impact/actions/{_ACTION_ID}/evidence",
        json={
            "evidence_type": "OFFICIAL_GAZETTE_DECREE",
            "evidence_title": "Resmi Gazete Kararı No 32155",
            "source_url": "https://resmigazete.gov.tr/karar-32155",
            "raw_document_content": "Cumhurbaşkanlığı Kararnamesi ile öğrenci indirimi yürürlüğe girmiştir.",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["action_id"] == str(_ACTION_ID)
    assert data["evidence_type"] == "OFFICIAL_GAZETTE_DECREE"
    assert data["evidence_title"] == "Resmi Gazete Kararı No 32155"
    assert data["source_url"] == "https://resmigazete.gov.tr/karar-32155"
    assert len(data["sha256_digest"]) == 64
    assert data["verification_status"] == "VERIFIED_AUTHENTIC"


def test_verify_action_impact_api() -> None:
    app = _make_app()
    client = TestClient(app)

    res = client.post(
        f"/v1/impact/actions/{_ACTION_ID}/verify",
        json={
            "outcome_verdict": "FULL_RESOLUTION",
            "resolution_score": 0.95,
            "auditor_consensus_count": 3,
            "verification_notes": "Tüm taahhütler mevzuata işlenerek tamamlanmıştır.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["action_id"] == str(_ACTION_ID)
    assert data["outcome_verdict"] == "FULL_RESOLUTION"
    assert data["resolution_score"] == 0.95
    assert data["auditor_consensus_count"] == 3

    # Verify action progress updated to 95 and VERIFIED_COMPLETE
    actions_res = client.get(f"/v1/impact/actions?case_version_id={_CASE_ID}")
    assert actions_res.status_code == 200
    actions = actions_res.json()
    target_action = next(a for a in actions if a["action_id"] == str(_ACTION_ID))
    assert target_action["status"] == "VERIFIED_COMPLETE"
    assert target_action["progress_percentage"] == 95


def test_trigger_response_reweigh_api() -> None:
    app = _make_app()
    client = TestClient(app)

    res = client.post(f"/v1/impact/institution-responses/{_RESP_ID}/reweigh")
    assert res.status_code == 200
    data = res.json()
    assert data["response_id"] == str(_RESP_ID)
    assert data["case_version_id"] == str(_CASE_ID)
    assert data["is_reweigh_active"] is True
    assert "reweigh-" in data["reweigh_round_id"]
    assert "Ulaştırma ve Altyapı Bakanlığı" in data["instructions"]
