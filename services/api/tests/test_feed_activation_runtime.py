from __future__ import annotations

from datetime import UTC, datetime

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.feed_activation_runtime import (
    build_feed_activation_runtime,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    InMemoryIngestionWorkerRuntimeRegistry,
)
from kefe_api.modules.knowledge.feed_activation import (
    FeedActivationOutcome,
    InMemoryFeedPipelineDefinitionRepository,
)
from kefe_api.modules.knowledge.provider_control_memory import (
    InMemorySourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_http_auth import (
    InMemoryProviderHttpAuthRegistry,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    InMemoryProviderAdoptionRegistry,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapterFactory,
)
from kefe_api.modules.knowledge.source_evidence import (
    UnconfiguredRawSourceEvidenceStore,
)


class NoNetworkTransport:
    def execute(self, request):
        del request
        raise AssertionError("empty activation runtime must not execute network")


def test_memory_feed_activation_runtime_starts_empty_and_disabled() -> None:
    evidence = UnconfiguredRawSourceEvidenceStore()
    runtime = build_feed_activation_runtime(
        Settings(persistence_backend="memory"),
        providers=InMemorySourceProviderAdmissionRepository(),
        adoption_profiles=InMemoryProviderAdoptionRegistry(),
        auth_profiles=InMemoryProviderHttpAuthRegistry(),
        evidence_store=evidence,
        public_http_factory=EvidenceBackedPublicHttpCaptureAdapterFactory(
            transport=NoNetworkTransport(),  # type: ignore[arg-type]
            evidence_store=evidence,
        ),
        ingestion_runtime=InMemoryIngestionWorkerRuntimeRegistry(),
    )

    assert isinstance(
        runtime.definitions,
        InMemoryFeedPipelineDefinitionRepository,
    )
    assert runtime.definitions.count == 0
    result = runtime.service.preflight(
        "feed.not_registered.v1",
        at=datetime(2026, 8, 3, 4, 0, tzinfo=UTC),
    )
    assert result.outcome is FeedActivationOutcome.BLOCKED
    assert result.reason_code == "FEED_ACTIVATION_DEFINITION_NOT_FOUND"
    assert runtime.definitions.count == 0
