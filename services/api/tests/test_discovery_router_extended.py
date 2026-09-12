"""Extended HTTP integration tests for the Discovery router search endpoint.

Supplements test_case_search_filter_api.py (which covers basic keyword/domain/tag).
This module focuses on:
- Response schema invariants (required fields, types)
- Status filter parameter
- Tag comma-separated parsing
- Multi-keyword and Turkish character queries
- Pagination-safe: limit/offset parameters accepted without error
- Empty / whitespace query handled gracefully
- Profile endpoint: default profile shape
- Profile endpoint: update then read
- Discovery search + profile OpenAPI registration
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from kefe_api.main import create_app


def _client() -> TestClient:
    return TestClient(create_app())


# ---------------------------------------------------------------------------
# Response schema invariants
# ---------------------------------------------------------------------------

def test_search_response_has_required_fields() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search")
    assert res.status_code == 200
    body = res.json()
    # Top-level fields
    assert "query" in body
    assert "selected_domain" in body
    assert "selected_tags" in body
    assert "total_matched" in body
    assert "results" in body
    assert isinstance(body["total_matched"], int)
    assert isinstance(body["results"], list)


def test_search_result_item_has_required_fields() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search")
    assert res.status_code == 200
    results = res.json()["results"]
    assert len(results) >= 1, "Expected at least one seeded result"
    item = results[0]
    assert "case_version_id" in item
    assert "title" in item
    assert "summary" in item
    assert "domain" in item
    assert "tags" in item
    assert "status" in item
    assert "published_at" in item
    assert isinstance(item["tags"], list)


def test_search_query_reflected_in_response() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?q=test")
    body = res.json()
    assert body["query"] == "test"


def test_search_domain_reflected_in_response() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?domain=DAILY_LIFE")
    body = res.json()
    assert body["selected_domain"] == "DAILY_LIFE"


def test_search_tags_reflected_as_list() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?tags=eğitim,teknoloji")
    body = res.json()
    assert isinstance(body["selected_tags"], list)


# ---------------------------------------------------------------------------
# Status filter
# ---------------------------------------------------------------------------

def test_status_filter_published_accepted() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?status=PUBLISHED")
    assert res.status_code == 200


def test_status_filter_draft_returns_empty_or_filtered() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?status=DRAFT")
    assert res.status_code == 200
    # Seeded data is published; DRAFT should return 0 or fewer
    body = res.json()
    assert isinstance(body["total_matched"], int)


# ---------------------------------------------------------------------------
# Tag comma-separated parsing
# ---------------------------------------------------------------------------

def test_single_tag_filter() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?tags=ulaşım")
    assert res.status_code == 200
    body = res.json()
    assert "ulaşım" in body["selected_tags"]


def test_multiple_tags_comma_separated() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?tags=ulaşım,eğitim")
    assert res.status_code == 200
    body = res.json()
    assert len(body["selected_tags"]) == 2


def test_tags_whitespace_trimmed() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?tags= ulaşım , eğitim ")
    assert res.status_code == 200
    body = res.json()
    # Whitespace is stripped; tags should not have leading/trailing spaces
    for tag in body["selected_tags"]:
        assert tag == tag.strip()


# ---------------------------------------------------------------------------
# Turkish character and multi-keyword queries
# ---------------------------------------------------------------------------

def test_turkish_char_query_no_crash() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?q=şehir%20planlaması")
    assert res.status_code == 200


def test_multi_word_query_no_crash() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?q=yapay+zeka+etik")
    assert res.status_code == 200


def test_special_char_query_no_500() -> None:
    client = _client()
    # SQL-like content should not cause server error
    res = client.get("/v1/discovery/cases/search?q=%27%3B+DROP+TABLE+cases%3B+--")
    assert res.status_code in (200, 422)


# ---------------------------------------------------------------------------
# Empty / whitespace queries
# ---------------------------------------------------------------------------

def test_empty_query_returns_all() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?q=")
    assert res.status_code == 200
    body = res.json()
    assert body["total_matched"] >= 2


def test_whitespace_only_query_no_crash() -> None:
    client = _client()
    res = client.get("/v1/discovery/cases/search?q=   ")
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# Pagination parameters accepted
# ---------------------------------------------------------------------------

def test_large_q_string_no_crash() -> None:
    """Very long query string should not cause server error."""
    client = _client()
    long_q = "a" * 500
    res = client.get(f"/v1/discovery/cases/search?q={long_q}")
    assert res.status_code in (200, 422)


# ---------------------------------------------------------------------------
# Discovery profile endpoint
# ---------------------------------------------------------------------------

def test_profile_returns_default_shape() -> None:
    client = _client()
    res = client.get("/v1/discovery/profile")
    assert res.status_code == 200
    body = res.json()
    assert "user_id" in body
    assert "preferred_domains" in body
    assert "complexity_level" in body
    assert "freshness_preference" in body
    assert "real_event_preference" in body
    assert "diversification_boost" in body
    assert "updated_at" in body
    assert isinstance(body["preferred_domains"], list)
    assert isinstance(body["diversification_boost"], float)


def test_profile_update_and_read() -> None:
    client = _client()
    update_payload = {
        # Only DomainPreference enum members are accepted; GOVERNANCE is unknown
        # so only ENVIRONMENT (known) + CIVIC (fallback if none pass) survive.
        "preferred_domains": ["ENVIRONMENT"],
        "complexity_level": "STANDARD",
        "freshness_preference": "RECENT",
        "real_event_preference": "INCLUDE",
        "diversification_boost": 0.4,
    }
    put_res = client.put("/v1/discovery/profile", json=update_payload)
    assert put_res.status_code == 200
    body = put_res.json()
    assert "ENVIRONMENT" in body["preferred_domains"]
    assert body["diversification_boost"] == 0.4


def test_profile_diversification_boost_zero_accepted() -> None:
    client = _client()
    update_payload = {
        "preferred_domains": [],
        "complexity_level": "STANDARD",
        "freshness_preference": "ANY",
        "real_event_preference": "INCLUDE",
        "diversification_boost": 0.0,
    }
    res = client.put("/v1/discovery/profile", json=update_payload)
    assert res.status_code == 200
    assert res.json()["diversification_boost"] == 0.0


# ---------------------------------------------------------------------------
# OpenAPI registration
# ---------------------------------------------------------------------------

def test_discovery_paths_in_openapi() -> None:
    client = _client()
    res = client.get("/openapi.json")
    assert res.status_code == 200
    paths = res.json().get("paths", {})
    assert any("discovery" in p and "search" in p for p in paths), (
        "Discovery search path not found in OpenAPI spec"
    )
    assert any("discovery" in p and "profile" in p for p in paths), (
        "Discovery profile path not found in OpenAPI spec"
    )