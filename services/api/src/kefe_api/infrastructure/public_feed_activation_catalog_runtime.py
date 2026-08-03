from __future__ import annotations

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.postgres_public_feed_activation_catalog import (
    PostgresPublicFeedActivationCatalogRepository,
)
from kefe_api.modules.knowledge.public_feed_activation_catalog import (
    InMemoryPublicFeedActivationCatalogRepository,
    PublicFeedActivationCatalogRepository,
)


def build_public_feed_activation_catalog_repository(
    settings: Settings,
) -> PublicFeedActivationCatalogRepository:
    if settings.persistence_backend == "memory":
        return InMemoryPublicFeedActivationCatalogRepository()
    if not settings.database_url:
        raise RuntimeError(
            "KEFE_DATABASE_URL is required when persistence_backend=postgres"
        )
    return PostgresPublicFeedActivationCatalogRepository(
        build_engine(settings.database_url)
    )


__all__ = ["build_public_feed_activation_catalog_repository"]
