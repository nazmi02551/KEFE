from __future__ import annotations

from datetime import datetime

from kefe_api.infrastructure.provider_http_runtime import (
    ProviderHttpRuntimeComponents,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.knowledge.provider_control import ProviderCredentialMode
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    ControlledProviderHttpTransport,
    InMemoryProviderAdoptionRegistry,
    ProviderHttpObserver,
)
from kefe_api.modules.knowledge.provider_public_execution import (
    InMemoryPublicSourceCaptureRegistry,
    PermitBoundPublicCaptureExecutor,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapterFactory,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    ProviderPermitExecutionContextRepository,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import (
    StrictRssAtomCaptureDefinition,
)
from kefe_api.modules.knowledge.source_acquisition import (
    InMemorySourceCaptureRegistry,
    SourceAcquisitionObserver,
    SourceAcquisitionResult,
    SourceAcquisitionService,
)
from kefe_api.modules.knowledge.source_evidence import RawSourceEvidenceStore


class InvocationScopedPublicFeedManualCaptureRuntime:
    def __init__(
        self,
        *,
        http_runtime: ProviderHttpRuntimeComponents,
        http_observer: ProviderHttpObserver,
        evidence_store: RawSourceEvidenceStore,
        knowledge_repository: KnowledgeRepository,
        ingestion_service: IngestionOrchestrationService,
        provider_admission: SourceProviderAdmissionService,
        provider_contexts: ProviderPermitExecutionContextRepository,
        acquisition_observer: SourceAcquisitionObserver,
    ) -> None:
        self._http_runtime = http_runtime
        self._http_observer = http_observer
        self._evidence_store = evidence_store
        self._knowledge_repository = knowledge_repository
        self._ingestion_service = ingestion_service
        self._provider_admission = provider_admission
        self._provider_contexts = provider_contexts
        self._acquisition_observer = acquisition_observer

    def execute(
        self,
        *,
        definition: PublicFeedDefinition,
        trace_id: str,
        at: datetime,
    ) -> SourceAcquisitionResult:
        if type(definition) is not PublicFeedDefinition:
            raise ValueError("manual capture requires exact PublicFeedDefinition")
        profile = definition.to_adoption_profile()
        capability = definition.capability_template.instantiate(created_at=at)
        registered = self._provider_admission.register(
            adapter_code=capability.adapter_code,
            credential_mode=ProviderCredentialMode.PUBLIC,
            secret_ref=None,
            quota_limit=capability.quota_limit,
            quota_window_seconds=capability.quota_window_seconds,
            failure_threshold=capability.failure_threshold,
            circuit_open_seconds=capability.circuit_open_seconds,
            permit_ttl_seconds=capability.permit_ttl_seconds,
            created_at=capability.created_at,
        )
        if registered.immutable_configuration != capability.immutable_configuration:
            raise ValueError("public feed provider capability conflict")

        adoption_registry = InMemoryProviderAdoptionRegistry((profile,))
        transport = ControlledProviderHttpTransport(
            adoption_registry=adoption_registry,
            dns_resolver=self._http_runtime.dns_resolver,
            backend=self._http_runtime.backend,
            observer=self._http_observer,
        )
        adapter = EvidenceBackedPublicHttpCaptureAdapterFactory(
            transport=transport,
            evidence_store=self._evidence_store,
        ).create(
            StrictRssAtomCaptureDefinition(
                adapter_code=definition.adapter_code,
                profile=definition.parser_profile,
            )
        )
        capture_registry = InMemoryPublicSourceCaptureRegistry((adapter,))
        capture_executor = PermitBoundPublicCaptureExecutor(
            contexts=self._provider_contexts,
            adapters=capture_registry,
        )
        acquisition = SourceAcquisitionService(
            knowledge_repository=self._knowledge_repository,
            ingestion_service=self._ingestion_service,
            registry=InMemorySourceCaptureRegistry(),
            observer=self._acquisition_observer,
            admission=self._provider_admission,
            capture_executor=capture_executor,
            clock=lambda: at,
        )
        return acquisition.acquire(
            definition.acquisition_command(),
            trace_id=trace_id,
        )


__all__ = ["InvocationScopedPublicFeedManualCaptureRuntime"]
