from __future__ import annotations

from dataclasses import dataclass

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.canonical_public_feed_runtime import (
    CanonicalPublicFeedRuntimeProfileRegistry,
    MutableProviderAdoptionRegistry,
    MutablePublicSourceCaptureRegistry,
)
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.editorial_pipeline import EditorialPipeline
from kefe_api.infrastructure.postgres_canonical_public_feed_catalog import (
    PostgresCanonicalPublicFeedCatalogRepository,
)
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.knowledge.canonical_public_feed_catalog import (
    CanonicalPublicFeedCatalogService,
    InMemoryPublicFeedCatalogRepository,
    PublicFeedCatalogRepository,
)


@dataclass(frozen=True, slots=True)
class CanonicalPublicFeedComposition:
    repository: PublicFeedCatalogRepository
    runtime_profiles: CanonicalPublicFeedRuntimeProfileRegistry
    service: CanonicalPublicFeedCatalogService


def build_canonical_public_feed_composition(
    settings: Settings,
    *,
    admin_security_service: AdminSecurityService,
    editorial_pipeline: EditorialPipeline,
) -> CanonicalPublicFeedComposition:
    if settings.persistence_backend == "memory":
        repository: PublicFeedCatalogRepository = InMemoryPublicFeedCatalogRepository()
    else:
        if not settings.database_url:
            raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")
        repository = PostgresCanonicalPublicFeedCatalogRepository(
            build_engine(settings.database_url)
        )

    adoption = editorial_pipeline.provider_adoption_registry
    capture = editorial_pipeline.public_capture_registry
    if not isinstance(adoption, MutableProviderAdoptionRegistry):
        raise RuntimeError("canonical public-feed composition requires mutable adoption registry")
    if not isinstance(capture, MutablePublicSourceCaptureRegistry):
        raise RuntimeError("canonical public-feed composition requires mutable capture registry")

    runtime_profiles = CanonicalPublicFeedRuntimeProfileRegistry(
        adoption=adoption,
        capture=capture,
        adapter_factory=editorial_pipeline.public_http_capture_adapter_factory,
    )
    service = CanonicalPublicFeedCatalogService(
        repository=repository,
        security=admin_security_service,
        provider_admission=editorial_pipeline.source_provider_admission_service,
        runtime_profiles=runtime_profiles,
        scheduler=editorial_pipeline.source_scheduler_service,
    )
    service.rehydrate_runtime_profiles()
    return CanonicalPublicFeedComposition(
        repository=repository,
        runtime_profiles=runtime_profiles,
        service=service,
    )


__all__ = [
    "CanonicalPublicFeedComposition",
    "build_canonical_public_feed_composition",
]
