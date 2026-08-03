from __future__ import annotations

from kefe_api.modules.ingestion_orchestration.feed_item_materializer import (
    FeedItemProposalMaterializer,
)


def test_feed_item_materialization_module_is_importable() -> None:
    assert FeedItemProposalMaterializer.__name__ == (
        "FeedItemProposalMaterializer"
    )
