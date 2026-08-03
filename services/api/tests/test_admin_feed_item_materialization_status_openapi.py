from __future__ import annotations

import pytest

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app


def test_feed_item_materialization_status_openapi_is_exact_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    get_settings.cache_clear()
    try:
        schema = create_app().openapi()
        path = (
            "/internal/admin/v1/proposals/{proposal_id}/"
            "feed-item-materialization-status"
        )
        assert path in schema["paths"]
        operation = schema["paths"][path]
        assert set(operation) == {"get"}
        get = operation["get"]
        assert get["tags"] == ["Internal Admin"]
        assert "requestBody" not in get
        assert all(parameter["in"] != "header" for parameter in get["parameters"])
        response_schema = get["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        assert response_schema == {
            "$ref": "#/components/schemas/FeedItemMaterializationStatusResponse"
        }

        response = schema["components"]["schemas"][
            "FeedItemMaterializationStatusResponse"
        ]
        expected = {
            "proposal_id",
            "status",
            "proposal_review_decision_id",
            "proposal_review_decision",
            "proposal_materialization_id",
            "target_kind",
            "target_id",
            "materialized_at",
        }
        assert set(response["required"]) == expected
        assert set(response["properties"]) == expected
        assert response["additionalProperties"] is False
        forbidden = {
            "payload",
            "normalized_text",
            "text",
            "metadata",
            "reviewer_ref",
            "rationale",
            "feed_storage_ref",
            "evidence_bytes",
            "object_key",
        }
        assert forbidden.isdisjoint(response["properties"])
    finally:
        get_settings.cache_clear()
