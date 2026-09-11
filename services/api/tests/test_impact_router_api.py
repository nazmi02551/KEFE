"""HTTP integration tests for the Impact router (CAP-048, CAP-050, CAP-051).

Covers:
- GET /v1/impact/institution-responses — empty list, no auth required
- GET /v1/impact/institution-responses?case_version_id=... — filter works
- GET /v1/impact/actions — empty list, no auth required
- GET /v1/impact/actions?case_version_id=... — filter works
- POST /v1/impact/actions — propose milestone, shape contract
- PATCH /v1/impact/actions/{id}/progress — update progress percentage
- Progress validation: 0..100 accepted, out-of-range rejected
- Action status lifecycle: PROPOSED → IN_PROGRESS → VERIFIED_COMPLETE
- Multiple actions for same case_version_id are all returned
- case_version_id filter excludes other cases
"""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.impact.in_memory import InMemoryImpactRepository

_CASE_A = uuid.UUID("11111111-1111-4111-8111-111111111111")
_CASE_B = uuid.UUID("22222222-2222-4222-8222-222222222222")


def _make_client(empty: bool = True) -> TestClient:
    app = create_app()
    if empty:
        app.state.impact_repository = InMemoryImpactRepository()
    return TestClient(app)


# ---------------------------------------------------------------------------
# Institution responses
# ---------------------------------------------------------------------------

def test_list_institution_responses_empty() -> None:
    client = _make_client()
    res = client.get("/v1/impact/institution-responses")
    assert res.status_code == 200
    assert res.json() == []


def test_list_institution_responses_with_unknown_filter() -> None:
    client = _make_client()
    res = client.get(f"/v1/impact/institution-responses?case_version_id={_CASE_A}")
    assert res.status_code == 200
    assert res.json() == []


def test_list_institution_responses_malformed_uuid() -> None:
    client = _make_client()
    res = client.get("/v1/impact/institution-responses?case_version_id=not-a-uuid")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Actions — list
# ---------------------------------------------------------------------------

def test_list_actions_empty() -> None:
    client = _make_client()
    res = client.get("/v1/impact/actions")
    assert res.status_code == 200
    assert res.json() == []


def test_list_actions_with_unknown_case_version_id() -> None:
    client = _make_client()
    res = client.get(f"/v1/impact/actions?case_version_id={_CASE_A}")
    assert res.status_code == 200
    assert res.json() == []


def test_list_actions_malformed_case_version_id() -> None:
    client = _make_client()
    res = client.get("/v1/impact/actions?case_version_id=not-a-uuid")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Actions — propose (POST)
# ---------------------------------------------------------------------------

def test_propose_action_returns_201() -> None:
    client = _make_client()
    res = client.post(
        "/v1/impact/actions",
        json={
            "case_version_id": str(_CASE_A),
            "title": "İlk eylem taslağı",
            "description": "Belediye meclisine bildirim gönderilmesi ve takip edilmesi",
        },
    )
    assert res.status_code == 201


def test_propose_action_response_shape() -> None:
    client = _make_client()
    res = client.post(
        "/v1/impact/actions",
        json={
            "case_version_id": str(_CASE_A),
            "title": "Eylem başlığı",
            "description": "Eylem açıklaması detaylı açıklama metni buraya girilir",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert "action_id" in body
    assert body["case_version_id"] == str(_CASE_A)
    assert body["title"] == "Eylem başlığı"
    assert body["status"] == "PROPOSED"
    assert body["progress_percentage"] == 0


def test_propose_action_then_list() -> None:
    client = _make_client()
    client.post(
        "/v1/impact/actions",
        json={
            "case_version_id": str(_CASE_A),
            "title": "Eylem 1",
            "description": "Detaylı eylem açıklaması burada yer alır",
        },
    )
    res = client.get("/v1/impact/actions")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_case_version_id_filter_excludes_other_cases() -> None:
    client = _make_client()
    # Add two actions for different cases
    for case, title in [(_CASE_A, "Case A action"), (_CASE_B, "Case B action")]:
        client.post(
            "/v1/impact/actions",
            json={
                "case_version_id": str(case),
                "title": title,
                "description": "Detaylı eylem test açıklaması burada yer alır",
            },
        )
    # Filter by case A — should return only 1
    res = client.get(f"/v1/impact/actions?case_version_id={_CASE_A}")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["case_version_id"] == str(_CASE_A)


def test_multiple_actions_for_same_case_all_returned() -> None:
    client = _make_client()
    for i in range(3):
        client.post(
            "/v1/impact/actions",
            json={
                "case_version_id": str(_CASE_A),
                "title": f"Eylem {i + 1}",
                "description": "Detaylı eylem test açıklaması burada yer alır",
            },
        )
    res = client.get(f"/v1/impact/actions?case_version_id={_CASE_A}")
    assert res.status_code == 200
    assert len(res.json()) == 3


# ---------------------------------------------------------------------------
# Actions — update progress (PATCH)
# ---------------------------------------------------------------------------

def _create_action(client: TestClient, case_id: uuid.UUID = _CASE_A) -> str:
    res = client.post(
        "/v1/impact/actions",
        json={
            "case_version_id": str(case_id),
            "title": "Test eylem",
            "description": "Detaylı eylem test açıklaması burada yer alır",
        },
    )
    assert res.status_code == 201
    return res.json()["action_id"]


def test_update_progress_to_50_in_progress() -> None:
    client = _make_client()
    action_id = _create_action(client)
    res = client.patch(
        f"/v1/impact/actions/{action_id}/progress",
        json={
            "case_version_id": str(_CASE_A),
            "progress_percentage": 50,
            "status": "IN_PROGRESS",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["progress_percentage"] == 50
    assert body["status"] == "IN_PROGRESS"


def test_update_progress_to_100_verified_complete() -> None:
    client = _make_client()
    action_id = _create_action(client)
    res = client.patch(
        f"/v1/impact/actions/{action_id}/progress",
        json={
            "case_version_id": str(_CASE_A),
            "progress_percentage": 100,
            "status": "VERIFIED_COMPLETE",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["progress_percentage"] == 100
    assert body["status"] == "VERIFIED_COMPLETE"


def test_update_progress_boundary_0_accepted() -> None:
    client = _make_client()
    action_id = _create_action(client)
    res = client.patch(
        f"/v1/impact/actions/{action_id}/progress",
        json={
            "case_version_id": str(_CASE_A),
            "progress_percentage": 0,
            "status": "PROPOSED",
        },
    )
    assert res.status_code == 200


@pytest.mark.parametrize("pct", [-1, 101, 150])
def test_update_progress_out_of_range_rejected(pct: int) -> None:
    client = _make_client()
    action_id = _create_action(client)
    res = client.patch(
        f"/v1/impact/actions/{action_id}/progress",
        json={
            "case_version_id": str(_CASE_A),
            "progress_percentage": pct,
            "status": "IN_PROGRESS",
        },
    )
    assert res.status_code == 422


def test_update_unknown_action_returns_404() -> None:
    client = _make_client()
    unknown_id = str(uuid.uuid4())
    res = client.patch(
        f"/v1/impact/actions/{unknown_id}/progress",
        json={
            "case_version_id": str(_CASE_A),
            "progress_percentage": 50,
            "status": "IN_PROGRESS",
        },
    )
    assert res.status_code == 404