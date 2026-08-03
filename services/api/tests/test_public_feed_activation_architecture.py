from __future__ import annotations

from kefe_api.modules.knowledge.public_feed_activation import (
    InMemoryPublicFeedActivationRegistry,
)


def test_production_default_activation_registry_is_empty() -> None:
    registry = InMemoryPublicFeedActivationRegistry()
    for identity in (
        "test.public_feed_activation.v1",
        "test.public_feed_adapter.v1",
    ):
        try:
            registry.get(identity)
        except KeyError:
            pass
        else:
            raise AssertionError("empty activation registry unexpectedly resolved identity")
