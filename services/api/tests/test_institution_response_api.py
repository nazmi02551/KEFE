from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.impact.in_memory import InMemoryImpactRepository
from kefe_api.modules.impact.models import (
    AuthorityVerificationStatus,
    InstitutionResponse,
    InstitutionResponseType,
)

_CASE_ID_1 = UUID("22222222-2222-4222-8222-222222222222")
_CASE_ID_2 = UUID("22222222-2222-4222-8222-222222222223")

_SEED_RESPONSES = [
    InstitutionResponse(
        response_id=uuid4(),
        case_version_id=_CASE_ID_1,
        institution_name="Ulaştırma ve Altyapı Denetleme Kurulu",
        authority_role="Halkla İlişkiler ve Yolcu Hakları Dairesi",
        verification_status=AuthorityVerificationStatus.VERIFIED,
        response_type=InstitutionResponseType.POLICY_CHANGE,
        statement="Topluluk müzakereleri ve yüksek uzlaşı verileri dikkate alınarak öncelikli yolcu kontenjanı genelgeye eklenmiştir.",
        published_at=datetime(2026, 8, 20, 10, 0, 0, tzinfo=UTC),
    ),
    InstitutionResponse(
        response_id=uuid4(),
        case_version_id=_CASE_ID_2,
        institution_name="Kişisel Verileri Koruma Kurumu (KVKK)",
        authority_role="Veri Güvenliği ve Yapay Zekâ İzleme Masası",
        verification_status=AuthorityVerificationStatus.VERIFIED,
        response_type=InstitutionResponseType.COMMITMENT,
        statement="Model eğitimi amaçlı veri toplama süreçlerine ilişkin şeffaflık kılavuzu taslağı kamuoyu görüşüne açılmıştır.",
        published_at=datetime(2026, 8, 25, 14, 0, 0, tzinfo=UTC),
    ),
]


def _make_app():
    app = create_app()
    repo = InMemoryImpactRepository()
    for r in _SEED_RESPONSES:
        repo.save_institution_response(r)
    app.state.impact_repository = repo
    return app


def test_list_institution_responses_empty() -> None:
    """With no data in repository the endpoint returns an empty list."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/v1/impact/institution-responses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_institution_responses_endpoint() -> None:
    app = _make_app()
    client = TestClient(app)

    response = client.get("/v1/impact/institution-responses")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2

    first = data[0]
    assert "response_id" in first
    assert "case_version_id" in first
    assert "institution_name" in first
    assert "statement" in first
    assert first["verification_status"] == "VERIFIED"
    assert first["response_type"] in [
        "POLICY_CHANGE",
        "COMMITMENT",
        "ACKNOWLEDGE",
    ]


def test_filter_institution_responses_by_case() -> None:
    app = _make_app()
    client = TestClient(app)

    target_case = str(_CASE_ID_1)
    response = client.get(
        f"/v1/impact/institution-responses?case_version_id={target_case}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    for item in data:
        assert item["case_version_id"] == target_case


def test_unverified_response_not_in_list() -> None:
    """PENDING_VERIFICATION responses must not appear in verified list."""
    app = create_app()
    repo = InMemoryImpactRepository()
    pending = InstitutionResponse(
        response_id=uuid4(),
        case_version_id=_CASE_ID_1,
        institution_name="Bekleyen Kurum",
        authority_role="Birim Amiri",
        verification_status=AuthorityVerificationStatus.PENDING_VERIFICATION,
        response_type=InstitutionResponseType.ACKNOWLEDGE,
        statement="İnceleme sürecindedir.",
        published_at=datetime.now(UTC),
    )
    repo.save_institution_response(pending)
    app.state.impact_repository = repo
    client = TestClient(app)

    response = client.get(
        f"/v1/impact/institution-responses?case_version_id={_CASE_ID_1}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0