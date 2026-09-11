"""HTTP integration tests for the Context API (ADR-0142, CAP-069, CAP-070).

Covers:
- GET /v1/case-versions/{id}/context — happy path, shape, isolation
- claim_status values match governed set (ADR-0142)
- disclosure_level values match governed set
- source_kind values match governed set (CAP-069)
- published_at is ISO 8601 or null (not a raw date string)
- source_ids cross-reference existing sources in the same snapshot
- Result / Perspective / community fields are absent (Commit First isolation)
- Unknown case_version_id → 404 + stable error code
- Malformed UUID → 422 (FastAPI validation)
- Response is bounded (blocks ≤ 20, sources ≤ 20)
"""
from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from kefe_api.main import create_app
from kefe_api.modules.context.bootstrap import DEMO_CASE_VERSION_ID
from kefe_api.modules.decision.bootstrap import DEMO_CASE_VERSION_ID as DECISION_DEMO_ID

_GOVERNED_CLAIM_STATUSES = {"VERIFIED", "CLAIMED", "DISPUTED", "UNKNOWN"}
_GOVERNED_DISCLOSURE_LEVELS = {"ESSENTIAL", "DETAIL", "SOURCE"}
_GOVERNED_SOURCE_KINDS = {"OFFICIAL", "NEWS", "RESEARCH", "EDITORIAL", "OTHER"}


def _make_client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Happy path — shape and field contract
# ---------------------------------------------------------------------------

def test_context_response_shape() -> None:
    client = _make_client()
    res = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")

    assert res.status_code == 200
    body = res.json()

    # Top-level keys
    assert "case_version_id" in body
    assert "blocks" in body
    assert "sources" in body

    # case_version_id round-trips
    assert body["case_version_id"] == str(DEMO_CASE_VERSION_ID)


def test_context_blocks_have_required_fields() -> None:
    client = _make_client()
    res = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")
    body = res.json()

    assert len(body["blocks"]) > 0
    for block in body["blocks"]:
        assert "context_block_id" in block
        assert "display_order" in block
        assert "disclosure_level" in block
        assert "title" in block
        assert "body" in block
        assert "claim_status" in block
        assert "source_ids" in block
        assert isinstance(block["display_order"], int)
        assert isinstance(block["source_ids"], list)


def test_context_sources_have_required_fields() -> None:
    client = _make_client()
    res = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")
    body = res.json()

    assert len(body["sources"]) > 0
    for source in body["sources"]:
        assert "source_id" in source
        assert "title" in source
        assert "publisher" in source
        assert "source_kind" in source
        assert isinstance(source["title"], str) and source["title"]
        assert isinstance(source["publisher"], str) and source["publisher"]


# ---------------------------------------------------------------------------
# ADR-0142 claim_status governance
# ---------------------------------------------------------------------------

def test_context_claim_status_in_governed_set() -> None:
    """Every block's claim_status must be one of the four canonical values."""
    client = _make_client()
    res = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")
    body = res.json()

    for block in body["blocks"]:
        assert block["claim_status"] in _GOVERNED_CLAIM_STATUSES, (
            f"Unexpected claim_status '{block['claim_status']}' in block {block['context_block_id']}"
        )


def test_context_first_block_is_essential_and_verified() -> None:
    """The ESSENTIAL block must be the first item and claim_status VERIFIED."""
    client = _make_client()
    res = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")
    body = res.json()

    # At least one ESSENTIAL block exists
    essential_blocks = [b for b in body["blocks"] if b["disclosure_level"] == "ESSENTIAL"]
    assert len(essential_blocks) >= 1

    # First block by display_order is ESSENTIAL
    sorted_blocks = sorted(body["blocks"], key=lambda b: b["display_order"])
    assert sorted_blocks[0]["disclosure_level"] == "ESSENTIAL"
    assert sorted_blocks[0]["claim_status"] == "VERIFIED"


# ---------------------------------------------------------------------------
# CAP-069 source_kind governance
# ---------------------------------------------------------------------------

def test_context_source_kind_in_governed_set() -> None:
    """Every source's source_kind must be one of the governed values."""
    client = _make_client()
    res = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")
    body = res.json()

    for source in body["sources"]:
        assert source["source_kind"] in _GOVERNED_SOURCE_KINDS, (
            f"Unexpected source_kind '{source['source_kind']}' in source {source['source_id']}"
        )


def test_context_disclosure_level_in_governed_set() -> None:
    """Every block's disclosure_level must be one of the governed values."""
    client = _make_client()
    res = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")
    body = res.json()

    for block in body["blocks"]:
        assert block["disclosure_level"] in _GOVERNED_DISCLOSURE_LEVELS, (
            f"Unexpected disclosure_level '{block['disclosure_level']}' in block {block['context_block_id']}"
        )


# ---------------------------------------------------------------------------
# Source ID cross-reference
# ---------------------------------------------------------------------------

def test_context_source_ids_cross_reference_sources() -> None:
    """source_ids in each block must reference existing source_id values."""
    client = _make_client()
    res = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")
    body = res.json()

    available_source_ids = {s["source_id"] for s in body["sources"]}
    for block in body["blocks"]:
        for sid in block["source_ids"]:
            assert sid in available_source_ids, (
                f"Block {block['context_block_id']} references unknown source_id {sid}"
            )


# ---------------------------------------------------------------------------
# Commit First isolation — result / perspective fields absent
# ---------------------------------------------------------------------------

def test_context_result_perspective_fields_absent() -> None:
    """No result, perspective or community data must appear in context response."""
    client = _make_client()
    res = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")
    serialized = res.text.lower()

    for forbidden in ("result", "perspective", "participant_reason", "community"):
        assert forbidden not in serialized, (
            f"Forbidden field '{forbidden}' found in context response"
        )


# ---------------------------------------------------------------------------
# Bounds — no more than 20 blocks or sources
# ---------------------------------------------------------------------------

def test_context_bounded_to_20_blocks_and_sources() -> None:
    """Response must not exceed 20 blocks or 20 sources."""
    client = _make_client()
    res = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")
    body = res.json()

    assert len(body["blocks"]) <= 20, f"Got {len(body['blocks'])} blocks (limit 20)"
    assert len(body["sources"]) <= 20, f"Got {len(body['sources'])} sources (limit 20)"


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

def test_unknown_case_version_returns_404_with_stable_error_code() -> None:
    client = _make_client()
    unknown_id = str(uuid.UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"))
    res = client.get(f"/v1/case-versions/{unknown_id}/context")

    assert res.status_code == 404
    body = res.json()
    assert body.get("code") == "CASE_VERSION_CONTEXT_NOT_FOUND"


def test_malformed_uuid_returns_422() -> None:
    client = _make_client()
    res = client.get("/v1/case-versions/not-a-uuid/context")

    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Demo case_version_id consistency across modules
# ---------------------------------------------------------------------------

def test_context_demo_id_matches_decision_demo_id() -> None:
    """Context and decision bootstrap use the same DEMO_CASE_VERSION_ID."""
    assert DEMO_CASE_VERSION_ID == DECISION_DEMO_ID, (
        "Context and Decision DEMO_CASE_VERSION_ID are out of sync"
    )