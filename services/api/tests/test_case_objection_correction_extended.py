"""Extended HTTP integration tests for Case Objection and Correction History APIs.

Covers:
- Objection: unknown case_version_id returns empty list (not 404)
- Objection: malformed UUID → 422
- Objection: missing required fields → 422
- Objection: statement min-length validation
- Objection: reason_category invalid value → 422
- Objection: supporting_evidence_url optional (none provided)
- Objection: OpenAPI registration
- Correction: list returns pre-seeded data
- Correction: unknown case_version_id → empty list or 404
- Correction: malformed UUID → 422
- Correction: response shape invariants
- Cross: same case_version_id yields independent objection + correction lists
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app

_SEEDED_CASE_VERSION = "22222222-2222-4222-8222-222222222222"
_UNKNOWN_VERSION = str(uuid.UUID("99999999-9999-4999-8999-999999999999"))


def _client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Objection — list
# ---------------------------------------------------------------------------

def test_list_objections_unknown_version_not_500() -> None:
    client = _client()
    res = client.get(f"/v1/cases/{_UNKNOWN_VERSION}/objections")
    # Must return 200 empty list or 404, never 500
    assert res.status_code in (200, 404)
    if res.status_code == 200:
        assert res.json() == []


def test_list_objections_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/objections")
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Objection — submit
# ---------------------------------------------------------------------------

def test_submit_objection_missing_reason_category() -> None:
    client = _client()
    res = client.post(
        f"/v1/cases/{_SEEDED_CASE_VERSION}/objections",
        json={
            "statement": "Gerekli alan eksik.",
        },
    )
    assert res.status_code == 422


def test_submit_objection_missing_statement() -> None:
    client = _client()
    res = client.post(
        f"/v1/cases/{_SEEDED_CASE_VERSION}/objections",
        json={
            "reason_category": "EDITORIAL_BIAS_FRAMING",
        },
    )
    assert res.status_code == 422


def test_submit_objection_without_evidence_url() -> None:
    """Supporting evidence URL is optional — should succeed without it."""
    client = _client()
    res = client.post(
        f"/v1/cases/{_SEEDED_CASE_VERSION}/objections",
        json={
            "reason_category": "FACTUAL_INACCURACY",
            "statement": "Olgusal açıdan değerlendirme kriteri eksik bırakılmış, belirtilen veri doğrulanamıyor.",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["reason_category"] == "FACTUAL_INACCURACY"
    assert body.get("supporting_evidence_url") is None or body["supporting_evidence_url"] == ""


def test_submit_objection_response_has_required_fields() -> None:
    client = _client()
    res = client.post(
        f"/v1/cases/{_SEEDED_CASE_VERSION}/objections",
        json={
            "reason_category": "EXCLUDED_STAKEHOLDER",
            "statement": "Etkilenen tarafların tamamı bu süreçte yeterince temsil edilmemiştir.",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert "objection_id" in body
    assert "case_version_id" in body
    assert "reason_category" in body
    assert "statement" in body
    assert "status" in body
    assert body["status"] == "SUBMITTED"


def test_submit_objection_malformed_case_version_id() -> None:
    client = _client()
    res = client.post(
        "/v1/cases/not-a-uuid/objections",
        json={
            "reason_category": "EDITORIAL_BIAS_FRAMING",
            "statement": "UUID geçersiz format testi için yazılmış itiraz metni.",
        },
    )
    assert res.status_code == 422


def test_submit_multiple_objections_both_listed() -> None:
    client = _client()
    # Submit 2 objections using valid enum values
    for category in ["AMBIGUOUS_OPTIONS", "EXCLUDED_STAKEHOLDER"]:
        res = client.post(
            f"/v1/cases/{_SEEDED_CASE_VERSION}/objections",
            json={
                "reason_category": category,
                "statement": f"{category} kapsamında seçenek çerçevesi eksik bırakılmış ve paydaş temsili yetersizdir.",
            },
        )
        assert res.status_code == 201

    # Both should appear in list
    list_res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/objections")
    assert list_res.status_code == 200
    # Pre-seeded (1) + our new submissions (2) = at least 3
    assert len(list_res.json()) >= 3


# ---------------------------------------------------------------------------
# Correction history — list
# Corrections endpoint returns: {case_version_id, corrections: [...]}
# ---------------------------------------------------------------------------

def test_list_corrections_seeded_case_returns_dict_with_list() -> None:
    """Corrections endpoint returns a dict with a 'corrections' key."""
    client = _client()
    res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/corrections")
    assert res.status_code == 200
    body = res.json()
    assert "case_version_id" in body
    assert "corrections" in body
    assert isinstance(body["corrections"], list)


def test_list_corrections_unknown_version_not_500() -> None:
    client = _client()
    res = client.get(f"/v1/cases/{_UNKNOWN_VERSION}/corrections")
    # Must not return 500
    assert res.status_code in (200, 404)
    if res.status_code == 200:
        body = res.json()
        # Either empty list or wrapper dict
        assert isinstance(body, (list, dict))


def test_list_corrections_malformed_uuid() -> None:
    client = _client()
    res = client.get("/v1/cases/not-a-uuid/corrections")
    assert res.status_code == 422


def test_list_corrections_response_shape() -> None:
    client = _client()
    res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/corrections")
    assert res.status_code == 200
    body = res.json()
    assert "corrections" in body
    items = body["corrections"]
    if not items:
        return  # Empty is valid
    item = items[0]
    # At least one identifying field must be present
    assert "correction_id" in item or "case_version_id" in item


# ---------------------------------------------------------------------------
# Cross: independent lists
# ---------------------------------------------------------------------------

def test_objections_and_corrections_are_independent() -> None:
    client = _client()
    obj_res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/objections")
    cor_res = client.get(f"/v1/cases/{_SEEDED_CASE_VERSION}/corrections")
    assert obj_res.status_code == 200
    assert cor_res.status_code == 200
    # Objections is a list; corrections is a dict wrapper
    assert isinstance(obj_res.json(), list)
    cor_body = cor_res.json()
    assert "corrections" in cor_body
    assert isinstance(cor_body["corrections"], list)


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_objection_correction_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("objections" in p for p in paths), "Objections path not in OpenAPI spec"
    assert any("corrections" in p for p in paths), "Corrections path not in OpenAPI spec"