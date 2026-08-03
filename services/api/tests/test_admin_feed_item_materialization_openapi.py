from __future__ import annotations

import pytest

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app


def test_feed_item_materialization_openapi_is_exact_and_bounded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "memory")
    get_settings.cache_clear()
    try:
        schema = create_app().openapi()
        path = (
            "/internal/admin/v1/proposals/{proposal_id}/"
            "feed-item-materialization"
        )
        assert path in schema["paths"]
        operation = schema["paths"][path]
        assert set(operation) == {"post"}
        post = operation["post"]
        assert post["tags"] == ["Internal Admin"]
        assert post["requestBody"]["required"] is True
        request_schema = post["requestBody"]["content"][
            "application/json"
        ]["schema"]
        assert request_schema == {
            "$ref": "#/components/schemas/FeedItemMaterializationRequest"
        }
        response_schema = post["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
        assert response_schema == {
            "$ref": "#/components/schemas/FeedItemMaterializationResponse"
        }

        components = schema["components"]["schemas"]
        request = components["FeedItemMaterializationRequest"]
        assert request["required"] == ["proposal_review_decision_id"]
        assert set(request["properties"]) == {"proposal_review_decision_id"}
        assert request["additionalProperties"] is False

        response = components["FeedItemMaterializationResponse"]
        expected = {
            "proposal_materialization_id",
            "proposal_id",
            "proposal_review_decision_id",
            "target_kind",
            "target_id",
            "materialized_at",
        }
        assert set(response["required"]) == expected
        assert set(response["properties"]) == expected
        assert response["additionalProperties"] is False
        forbidden = {
            "payload",
            "raw_xml",
            "evidence_bytes",
            "feed_storage_ref",
            "headers",
            "credentials",
            "object_key",
        }
        assert forbidden.isdisjoint(response["properties"])
    finally:
        get_settings.cache_clear()
