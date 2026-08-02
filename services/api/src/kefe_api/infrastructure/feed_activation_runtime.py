from __future__ import annotations

from dataclasses import dataclass

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.postgres_feed_activation import (
    PostgresFeedPipelineDefinitionRepository,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionWorkerRuntimeRegistry,
)
from kefe_api.modules.knowledge.feed_activation import (
    FeedActivationService,
    FeedParserProfileRegistry,
    FeedPipelineDefinitionRepository,
    InMemoryFeedParserProfileRegistry,
    InMemoryFeedPipelineDefinitionRepository,
)
from kefe_api.modules.knowledge.provider_control_ports import (
    SourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_http_auth import ProviderHttpAuthRegistry
from kefe_api.modules.knowledge.provider_http_transport import ProviderAdoptionRegistry
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapterFactory,
)
from kefe_api.modules.knowledge.source_evidence import RawSourceEvidenceStore


@dataclass(frozen=True, slots=True)
class FeedActivationRuntime:
    definitions: FeedPipelineDefinitionRepository
    parser_profiles: FeedParserProfileRegistry
    service: FeedActivationService


def build_feed_activation_runtime(
    settings: Settings,
    *,
    providers: SourceProviderAdmissionRepository,
    adoption_profiles: ProviderAdoptionRegistry,
    auth_profiles: ProviderHttpAuthRegistry,
    evidence_store: RawSourceEvidenceStore,
    public_http_factory: EvidenceBackedPublicHttpCaptureAdapterFactory,
    ingestion_runtime: IngestionWorkerRuntimeRegistry,
) -> FeedActivationRuntime:
    if settings.persistence_backend == "memory":
        definitions: FeedPipelineDefinitionRepository = (
            InMemoryFeedPipelineDefinitionRepository()
        )
    else:
        if not settings.database_url:
            raise RuntimeError(
                "KEFE_DATABASE_URL is required when persistence_backend=postgres"
            )
        definitions = PostgresFeedPipelineDefinitionRepository(
            build_engine(settings.database_url)
        )

    parser_profiles: FeedParserProfileRegistry = (
        InMemoryFeedParserProfileRegistry()
    )
    service = FeedActivationService(
        definitions=definitions,
        providers=providers,
        adoption_profiles=adoption_profiles,
        auth_profiles=auth_profiles,
        evidence_store=evidence_store,
        parser_profiles=parser_profiles,
        public_http_factory=public_http_factory,
        ingestion_runtime=ingestion_runtime,
    )
    return FeedActivationRuntime(
        definitions=definitions,
        parser_profiles=parser_profiles,
        service=service,
    )


__all__ = ["FeedActivationRuntime", "build_feed_activation_runtime"]
