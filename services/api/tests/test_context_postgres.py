from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from kefe_api.core.settings import get_settings
from kefe_api.main import create_app
from kefe_api.modules.context.bootstrap import (
    DEMO_CONTEXT_BLOCK_ID,
    DEMO_CONTEXT_DETAIL_ID,
    DEMO_CONTEXT_SOURCE_ID,
)
from kefe_api.modules.decision.bootstrap import DEMO_CASE_VERSION_ID

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def test_postgres_context_is_case_version_pinned_and_pre_commit_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    try:
        client = TestClient(create_app())
        response = client.get(f"/v1/case-versions/{DEMO_CASE_VERSION_ID}/context")
        assert response.status_code == 200

        body = response.json()
        assert body["case_version_id"] == str(DEMO_CASE_VERSION_ID)
        assert [block["context_block_id"] for block in body["blocks"]] == [
            str(DEMO_CONTEXT_BLOCK_ID),
            str(DEMO_CONTEXT_DETAIL_ID),
        ]
        assert body["blocks"][0]["claim_status"] == "VERIFIED"
        assert body["blocks"][1]["claim_status"] == "UNKNOWN"
        assert body["sources"][0]["source_id"] == str(DEMO_CONTEXT_SOURCE_ID)
        assert body["sources"][0]["source_kind"] == "EDITORIAL"

        serialized = response.text.lower()
        for forbidden in (
            "result",
            "perspective",
            "participant_reason",
            "community",
            "sample_size",
        ):
            assert forbidden not in serialized
    finally:
        get_settings.cache_clear()
