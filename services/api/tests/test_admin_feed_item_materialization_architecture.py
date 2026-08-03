from __future__ import annotations

from kefe_api.modules.admin_security.feed_item_materialization import (
    SecuredFeedItemMaterializationService,
)


def test_admin_feed_item_materialization_module_is_importable() -> None:
    assert SecuredFeedItemMaterializationService.__name__ == (
        "SecuredFeedItemMaterializationService"
    )
