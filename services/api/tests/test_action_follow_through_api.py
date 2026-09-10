from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.impact.in_memory import InMemoryImpactRepository

_CASE_ID = UUID("22222222-2222-4222-8222-222222222222")


def _make_app():
    app = create_app()
    # Start with an empty repository — actions are created via API
    app.state.impact_repository = InMemoryImpactRepository()
    return app


def test_list_actions_empty() -> None:
    """With no data the endpoint returns an empty list."""
    app = _make_app()
    client = TestClient(app)
    res = client.get("/v1/impact/actions")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_and_propose_actions_endpoint() -> None:
    app = _make_app()
    client = TestClient(app)

    case_version_id = str(_CASE_ID)

    # 1. Propose new action
    propose_res = client.post(
        "/v1/impact/actions",
        json={
            "case_version_id": case_version_id,
            "title": "Yeni Yurttaş İnisiyatifi ve İzleme Kurulu",
            "description": "Topluluk kararlarının yerel idareye iletilmesi ve aylık raporlama yapılması.",
        },
    )
    assert propose_res.status_code == 201
    action_data = propose_res.json()
    action_id = action_data["action_id"]
    assert action_data["status"] == "PROPOSED"
    assert action_data["progress_percentage"] == 0
    assert action_data["case_version_id"] == case_version_id

    # 2. List actions — should contain the proposed one
    res = client.get("/v1/impact/actions")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    first = data[0]
    assert "action_id" in first
    assert "title" in first
    assert first["status"] in [
        "PROPOSED",
        "IN_PROGRESS",
        "VERIFIED_COMPLETE",
        "STALLED",
    ]
    assert 0 <= first["progress_percentage"] <= 100

    # 3. Update progress with evidence
    patch_res = client.patch(
        f"/v1/impact/actions/{action_id}/progress",
        json={
            "case_version_id": case_version_id,
            "progress_percentage": 50,
            "status": "IN_PROGRESS",
            "evidence_summary": "İlk izleme toplantısı yapıldı ve tutanak tutuldu.",
            "evidence_url": "https://kefe.org/izleme/rapor-1",
        },
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["progress_percentage"] == 50
    assert updated_data["status"] == "IN_PROGRESS"
    assert updated_data["evidence_url"] == "https://kefe.org/izleme/rapor-1"


def test_propose_action_validation() -> None:
    """Short title/description rejected with 4xx (422 from Pydantic min_length)."""
    app = _make_app()
    client = TestClient(app)
    res = client.post(
        "/v1/impact/actions",
        json={
            "case_version_id": str(_CASE_ID),
            "title": "ab",  # too short — Pydantic min_length=3 → 422
            "description": "Topluluk kararlarının yerel idareye iletilmesi.",
        },
    )
    assert res.status_code in (400, 422)


def test_update_nonexistent_action_returns_404() -> None:
    """Updating a non-existent action returns 404."""
    app = _make_app()
    client = TestClient(app)
    fake_id = "ffffffff-ffff-4fff-8fff-ffffffffffff"
    res = client.patch(
        f"/v1/impact/actions/{fake_id}/progress",
        json={
            "case_version_id": str(_CASE_ID),
            "progress_percentage": 10,
            "status": "IN_PROGRESS",
        },
    )
    assert res.status_code == 404


def test_filter_actions_by_case() -> None:
    """Actions can be filtered by case_version_id."""
    app = _make_app()
    client = TestClient(app)
    case_id = str(_CASE_ID)
    other_case_id = "33333333-3333-4333-8333-333333333333"

    # Propose one action for each case
    client.post("/v1/impact/actions", json={
        "case_version_id": case_id,
        "title": "Birinci eylem planı",
        "description": "Belediye meclisine resmi dilekçe verilmesi gerekmektedir.",
    })
    client.post("/v1/impact/actions", json={
        "case_version_id": other_case_id,
        "title": "İkinci eylem planı",
        "description": "Farklı bir dava için yürütülen izleme sürecinin başlatılması.",
    })

    res = client.get(f"/v1/impact/actions?case_version_id={case_id}")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["case_version_id"] == case_id