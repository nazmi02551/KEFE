from __future__ import annotations

import pytest

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app

FEED_LIST = "/internal/admin/v1/feed-items"
FEED_DETAIL = "/internal/admin/v1/feed-items/{proposal_id}"
SOURCE_BRIEF_BUILD = "/internal/admin/v1/feed-items/{proposal_id}/source-brief"
SOURCE_BRIEF_LIST = "/internal/admin/v1/source-briefs"
SOURCE_BRIEF_DETAIL = "/internal/admin/v1/source-briefs/{proposal_id}"


def _openapi(monkeypatch: pytest.MonkeyPatch, version: str) -> dict[str, object]:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    monkeypatch.setenv("KEFE_API_VERSION", version)
    get_settings.cache_clear()
    try:
        return create_app().openapi()
    finally:
        get_settings.cache_clear()


def _methods(spec: dict[str, object], path: str) -> set[str]:
    paths = spec["paths"]
    assert isinstance(paths, dict)
    value = paths[path]
    assert isinstance(value, dict)
    return set(value) & {"get", "post", "put", "patch", "delete"}


def _path_set(spec: dict[str, object]) -> set[str]:
    paths = spec["paths"]
    assert isinstance(paths, dict)
    return set(paths)


def _schemas(spec: dict[str, object]) -> set[str]:
    components = spec["components"]
    assert isinstance(components, dict)
    schemas = components["schemas"]
    assert isinstance(schemas, dict)
    return set(schemas)


def test_admin_review_openapi_is_exactly_additive_from_020_to_023(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec_020 = _openapi(monkeypatch, "0.20.0")
    spec_021 = _openapi(monkeypatch, "0.21.0")
    spec_022 = _openapi(monkeypatch, "0.22.0")
    spec_023 = _openapi(monkeypatch, "0.23.0")

    new_paths = {
        FEED_LIST,
        FEED_DETAIL,
        SOURCE_BRIEF_BUILD,
        SOURCE_BRIEF_LIST,
        SOURCE_BRIEF_DETAIL,
    }
    assert _path_set(spec_020).isdisjoint(new_paths)

    assert _path_set(spec_021) - _path_set(spec_020) == {
        FEED_LIST,
        FEED_DETAIL,
    }
    assert _methods(spec_021, FEED_LIST) == {"get"}
    assert _methods(spec_021, FEED_DETAIL) == {"get"}
    assert SOURCE_BRIEF_BUILD not in _path_set(spec_021)
    assert SOURCE_BRIEF_LIST not in _path_set(spec_021)
    assert SOURCE_BRIEF_DETAIL not in _path_set(spec_021)

    assert _path_set(spec_022) - _path_set(spec_021) == {SOURCE_BRIEF_BUILD}
    assert _methods(spec_022, SOURCE_BRIEF_BUILD) == {"post"}
    assert SOURCE_BRIEF_LIST not in _path_set(spec_022)
    assert SOURCE_BRIEF_DETAIL not in _path_set(spec_022)

    assert _path_set(spec_023) - _path_set(spec_022) == {
        SOURCE_BRIEF_LIST,
        SOURCE_BRIEF_DETAIL,
    }
    assert _methods(spec_023, SOURCE_BRIEF_LIST) == {"get"}
    assert _methods(spec_023, SOURCE_BRIEF_DETAIL) == {"get"}

    assert {
        "FeedItemReviewSummaryResponse",
        "FeedItemReviewPageResponse",
        "FeedItemReviewDetailResponse",
    }.issubset(_schemas(spec_021))
    assert "SourceBriefIngestionResponse" in _schemas(spec_022)
    assert {
        "SourceBriefReviewSummaryResponse",
        "SourceBriefReviewPageResponse",
        "SourceBriefReviewDetailResponse",
    }.issubset(_schemas(spec_023))
