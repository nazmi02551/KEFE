from __future__ import annotations

from dataclasses import dataclass

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.postgres_content_supply_cycle import (
    PostgresContentSupplyCycleRepository,
)
from kefe_api.infrastructure.postgres_content_supply_health import (
    PostgresContentSupplyOperationalFactsRepository,
)
from kefe_api.infrastructure.postgres_editorial_projection import (
    PostgresEditorialProjectionRepository,
)
from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_ingestion_run_leases import (
    PostgresIngestionRunLeaseRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.infrastructure.postgres_proposal_review_queue import (
    PostgresProposalReviewQueueRepository,
)
from kefe_api.infrastructure.postgres_provider_execution_context import (
    PostgresProviderPermitExecutionContextRepository,
)
from kefe_api.infrastructure.postgres_source_acquisition_scheduler import (
    PostgresSourceAcquisitionSchedulerRepository,
)
from kefe_api.infrastructure.postgres_source_provider_admission import (
    PostgresSourceProviderAdmissionRepository,
)
from kefe_api.infrastructure.provider_http_runtime import build_provider_http_runtime
from kefe_api.modules.admin_security.editorial_projection import (
    SecuredEditorialProjectionService,
)
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_authoring.in_memory import (
    InMemoryContentAuthoringRepository,
)
from kefe_api.modules.content_authoring.ports import ContentAuthoringRepository
from kefe_api.modules.content_supply_cycle.in_memory import (
    InMemoryContentSupplyCycleRepository,
)
from kefe_api.modules.content_supply_cycle.ports import ContentSupplyCycleRepository
from kefe_api.modules.content_supply_cycle.service import (
    ContentSupplyCycleObserver,
    ContentSupplyCycleService,
    NoOpContentSupplyCycleObserver,
)
from kefe_api.modules.content_supply_health.in_memory import (
    InMemoryContentSupplyOperationalFactsRepository,
)
from kefe_api.modules.content_supply_health.ports import (
    ContentSupplyOperationalFactsRepository,
)
from kefe_api.modules.content_supply_health.service import ContentSupplyHealthService
from kefe_api.modules.editorial_projection.in_memory import (
    InMemoryEditorialProjectionProfileRegistry,
    InMemoryEditorialProjectionRepository,
)
from kefe_api.modules.editorial_projection.ingestion_source import (
    IngestionReviewedProposalSource,
)
from kefe_api.modules.editorial_projection.models import EditorialProjectionProfile
from kefe_api.modules.editorial_projection.ports import EditorialProjectionRepository
from kefe_api.modules.editorial_projection.service import EditorialProjectionService
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.in_memory_leases import (
    InMemoryIngestionRunLeaseRepository,
)
from kefe_api.modules.ingestion_orchestration.lease_ports import (
    IngestionRunLeaseRepository,
)
from kefe_api.modules.ingestion_orchestration.lease_service import (
    IngestionRunLeaseService,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
    ProposalReviewQueueRepository,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionWorkerObserver,
    IngestionWorkerRuntimeRegistry,
    InMemoryIngestionWorkerRuntimeRegistry,
    NoOpIngestionWorkerObserver,
)
from kefe_api.modules.ingestion_orchestration.worker_service import (
    IngestionWorkerRunner,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.knowledge.provider_control_memory import (
    InMemorySourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control_ports import (
    SourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.provider_http_auth import (
    InMemoryProviderHttpAuthRegistry,
    ProviderHttpAuthRegistry,
    SecureProviderHttpExecutor,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    ControlledProviderHttpTransport,
    InMemoryProviderAdoptionRegistry,
    NoOpProviderHttpObserver,
    ProviderAdoptionRegistry,
    ProviderHttpObserver,
)
from kefe_api.modules.knowledge.provider_public_execution import (
    CredentialModeRoutingProviderCaptureExecutor,
    InMemoryPublicSourceCaptureRegistry,
    PermitBoundPublicCaptureExecutor,
    PublicSourceCaptureRegistry,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapterFactory,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    CredentialAwareSourceCaptureRegistry,
    InMemoryCredentialAwareSourceCaptureRegistry,
    InMemorySecretResolverRegistry,
    ProviderPermitExecutionContextRepository,
    SecretResolverRegistry,
    SecureProviderCaptureExecutor,
)
from kefe_api.modules.knowledge.source_acquisition import (
    InMemorySourceCaptureRegistry,
    NoOpSourceAcquisitionObserver,
    SourceAcquisitionObserver,
    SourceAcquisitionService,
    SourceCaptureRegistry,
)
from kefe_api.modules.knowledge.source_evidence import RawSourceEvidenceStore
from kefe_api.modules.knowledge.source_scheduler_memory import (
    InMemorySourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.knowledge.source_scheduler_ports import (
    SourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    NoOpSourceDispatchObserver,
    SourceAcquisitionSchedulerService,
    SourceDispatchObserver,
)


@dataclass(frozen=True, slots=True)
class EditorialPipeline:
    knowledge_repository: KnowledgeRepository
    source_capture_registry: SourceCaptureRegistry
    source_provider_admission_repository: SourceProviderAdmissionRepository
    source_provider_admission_service: SourceProviderAdmissionService
    provider_execution_context_repository: ProviderPermitExecutionContextRepository
    secret_resolver_registry: SecretResolverRegistry
    credential_capture_registry: CredentialAwareSourceCaptureRegistry
    secure_provider_capture_executor: SecureProviderCaptureExecutor
    public_capture_registry: PublicSourceCaptureRegistry
    public_provider_capture_executor: PermitBoundPublicCaptureExecutor
    provider_capture_executor: CredentialModeRoutingProviderCaptureExecutor
    provider_adoption_registry: ProviderAdoptionRegistry
    provider_http_auth_registry: ProviderHttpAuthRegistry
    provider_http_observer: ProviderHttpObserver
    provider_http_transport: ControlledProviderHttpTransport
    secure_provider_http_executor: SecureProviderHttpExecutor
    public_http_capture_adapter_factory: EvidenceBackedPublicHttpCaptureAdapterFactory
    source_acquisition_observer: SourceAcquisitionObserver
    source_acquisition_service: SourceAcquisitionService
    source_scheduler_repository: SourceAcquisitionSchedulerRepository
    source_dispatch_observer: SourceDispatchObserver
    source_scheduler_service: SourceAcquisitionSchedulerService
    ingestion_repository: IngestionOrchestrationRepository
    ingestion_service: IngestionOrchestrationService
    ingestion_lease_repository: IngestionRunLeaseRepository
    ingestion_lease_service: IngestionRunLeaseService
    ingestion_worker_registry: IngestionWorkerRuntimeRegistry
    ingestion_worker_observer: IngestionWorkerObserver
    ingestion_worker_runner: IngestionWorkerRunner
    content_supply_cycle_repository: ContentSupplyCycleRepository
    content_supply_cycle_observer: ContentSupplyCycleObserver
    content_supply_cycle_service: ContentSupplyCycleService
    content_supply_health_repository: ContentSupplyOperationalFactsRepository
    content_supply_health_service: ContentSupplyHealthService
    proposal_queue_repository: ProposalReviewQueueRepository
    projection_repository: EditorialProjectionRepository
    projection_service: EditorialProjectionService
    secured_projection_service: SecuredEditorialProjectionService


def build_editorial_pipeline(
    settings: Settings,
    *,
    content_authoring_repository: ContentAuthoringRepository,
    admin_security_service: AdminSecurityService,
    raw_source_evidence_store: RawSourceEvidenceStore,
) -> EditorialPipeline:
    if settings.persistence_backend == "memory":
        if not isinstance(
            content_authoring_repository,
            InMemoryContentAuthoringRepository,
        ):
            raise RuntimeError(
                "memory Editorial Projection requires in-memory Content Authoring"
            )
        knowledge_repository: KnowledgeRepository = InMemoryKnowledgeRepository()
        memory_provider_admission = InMemorySourceProviderAdmissionRepository()
        source_provider_admission_repository: SourceProviderAdmissionRepository = (
            memory_provider_admission
        )
        provider_execution_context_repository: (
            ProviderPermitExecutionContextRepository
        ) = memory_provider_admission
        memory_scheduler = InMemorySourceAcquisitionSchedulerRepository()
        source_scheduler_repository: SourceAcquisitionSchedulerRepository = (
            memory_scheduler
        )
        memory_cycles = InMemoryContentSupplyCycleRepository()
        content_supply_cycle_repository: ContentSupplyCycleRepository = memory_cycles
        memory_ingestion = InMemoryIngestionOrchestrationRepository()
        ingestion_repository: IngestionOrchestrationRepository = memory_ingestion
        memory_leases = InMemoryIngestionRunLeaseRepository(memory_ingestion)
        ingestion_lease_repository: IngestionRunLeaseRepository = memory_leases
        content_supply_health_repository: ContentSupplyOperationalFactsRepository = (
            InMemoryContentSupplyOperationalFactsRepository(
                scheduler=memory_scheduler,
                ingestion=memory_ingestion,
                leases=memory_leases,
                cycles=memory_cycles,
            )
        )
        proposal_queue_repository: ProposalReviewQueueRepository = memory_ingestion
        projection_repository: EditorialProjectionRepository = (
            InMemoryEditorialProjectionRepository(content_authoring_repository)
        )
    else:
        if not settings.database_url:
            raise RuntimeError(
                "KEFE_DATABASE_URL is required when persistence_backend=postgres"
            )
        engine = build_engine(settings.database_url)
        knowledge_repository = PostgresKnowledgeRepository(engine)
        source_provider_admission_repository = (
            PostgresSourceProviderAdmissionRepository(engine)
        )
        provider_execution_context_repository = (
            PostgresProviderPermitExecutionContextRepository(engine)
        )
        source_scheduler_repository = PostgresSourceAcquisitionSchedulerRepository(engine)
        content_supply_cycle_repository = PostgresContentSupplyCycleRepository(engine)
        content_supply_health_repository = (
            PostgresContentSupplyOperationalFactsRepository(engine)
        )
        ingestion_repository = PostgresIngestionOrchestrationRepository(engine)
        ingestion_lease_repository = PostgresIngestionRunLeaseRepository(engine)
        proposal_queue_repository = PostgresProposalReviewQueueRepository(engine)
        projection_repository = PostgresEditorialProjectionRepository(engine)

    ingestion_service = IngestionOrchestrationService(ingestion_repository)
    source_capture_registry: SourceCaptureRegistry = InMemorySourceCaptureRegistry()
    provider_admission_service = SourceProviderAdmissionService(
        source_provider_admission_repository
    )
    secret_resolver_registry: SecretResolverRegistry = InMemorySecretResolverRegistry()
    credential_capture_registry: CredentialAwareSourceCaptureRegistry = (
        InMemoryCredentialAwareSourceCaptureRegistry()
    )
    secure_provider_capture_executor = SecureProviderCaptureExecutor(
        contexts=provider_execution_context_repository,
        resolvers=secret_resolver_registry,
        adapters=credential_capture_registry,
    )
    public_capture_registry: PublicSourceCaptureRegistry = (
        InMemoryPublicSourceCaptureRegistry()
    )
    public_provider_capture_executor = PermitBoundPublicCaptureExecutor(
        contexts=provider_execution_context_repository,
        adapters=public_capture_registry,
    )
    provider_capture_executor = CredentialModeRoutingProviderCaptureExecutor(
        contexts=provider_execution_context_repository,
        public_executor=public_provider_capture_executor,
        credentialed_executor=secure_provider_capture_executor,
    )
    provider_adoption_registry: ProviderAdoptionRegistry = (
        InMemoryProviderAdoptionRegistry()
    )
    provider_http_auth_registry: ProviderHttpAuthRegistry = (
        InMemoryProviderHttpAuthRegistry()
    )
    provider_http_observer: ProviderHttpObserver = NoOpProviderHttpObserver()
    provider_http_runtime = build_provider_http_runtime(settings)
    provider_http_transport = ControlledProviderHttpTransport(
        adoption_registry=provider_adoption_registry,
        dns_resolver=provider_http_runtime.dns_resolver,
        backend=provider_http_runtime.backend,
        observer=provider_http_observer,
    )
    secure_provider_http_executor = SecureProviderHttpExecutor(
        auth_registry=provider_http_auth_registry,
        transport=provider_http_transport,
    )
    public_http_capture_adapter_factory = (
        EvidenceBackedPublicHttpCaptureAdapterFactory(
            transport=provider_http_transport,
            evidence_store=raw_source_evidence_store,
        )
    )
    source_acquisition_observer: SourceAcquisitionObserver = (
        NoOpSourceAcquisitionObserver()
    )
    source_acquisition_service = SourceAcquisitionService(
        knowledge_repository=knowledge_repository,
        ingestion_service=ingestion_service,
        registry=source_capture_registry,
        observer=source_acquisition_observer,
        admission=provider_admission_service,
        capture_executor=provider_capture_executor,
    )
    source_dispatch_observer: SourceDispatchObserver = NoOpSourceDispatchObserver()
    source_scheduler_service = SourceAcquisitionSchedulerService(
        repository=source_scheduler_repository,
        acquisition=source_acquisition_service,
        observer=source_dispatch_observer,
    )
    ingestion_lease_service = IngestionRunLeaseService(ingestion_lease_repository)
    ingestion_worker_registry: IngestionWorkerRuntimeRegistry = (
        InMemoryIngestionWorkerRuntimeRegistry()
    )
    ingestion_worker_observer: IngestionWorkerObserver = NoOpIngestionWorkerObserver()
    ingestion_worker_runner = IngestionWorkerRunner(
        repository=ingestion_repository,
        orchestration=ingestion_service,
        leases=ingestion_lease_service,
        registry=ingestion_worker_registry,
        observer=ingestion_worker_observer,
    )
    content_supply_cycle_observer: ContentSupplyCycleObserver = (
        NoOpContentSupplyCycleObserver()
    )
    content_supply_cycle_service = ContentSupplyCycleService(
        repository=content_supply_cycle_repository,
        scheduler=source_scheduler_service,
        ingestion_worker=ingestion_worker_runner,
        observer=content_supply_cycle_observer,
    )
    content_supply_health_service = ContentSupplyHealthService(
        content_supply_health_repository
    )

    profiles = InMemoryEditorialProjectionProfileRegistry(
        (
            EditorialProjectionProfile(
                profile_code="CANDIDATE_TO_AUTHORING",
                profile_version=1,
                candidate_schema_ref="kefe.candidate-case",
                candidate_schema_version="1.0.0",
                required_dependency_kinds=frozenset(
                    {"DECISION_PROBLEM", "QUESTION_DRAFT"}
                ),
            ),
        )
    )
    projection_service = EditorialProjectionService(
        IngestionReviewedProposalSource(ingestion_repository),
        profiles,
        projection_repository,
    )
    return EditorialPipeline(
        knowledge_repository=knowledge_repository,
        source_capture_registry=source_capture_registry,
        source_provider_admission_repository=source_provider_admission_repository,
        source_provider_admission_service=provider_admission_service,
        provider_execution_context_repository=provider_execution_context_repository,
        secret_resolver_registry=secret_resolver_registry,
        credential_capture_registry=credential_capture_registry,
        secure_provider_capture_executor=secure_provider_capture_executor,
        public_capture_registry=public_capture_registry,
        public_provider_capture_executor=public_provider_capture_executor,
        provider_capture_executor=provider_capture_executor,
        provider_adoption_registry=provider_adoption_registry,
        provider_http_auth_registry=provider_http_auth_registry,
        provider_http_observer=provider_http_observer,
        provider_http_transport=provider_http_transport,
        secure_provider_http_executor=secure_provider_http_executor,
        public_http_capture_adapter_factory=public_http_capture_adapter_factory,
        source_acquisition_observer=source_acquisition_observer,
        source_acquisition_service=source_acquisition_service,
        source_scheduler_repository=source_scheduler_repository,
        source_dispatch_observer=source_dispatch_observer,
        source_scheduler_service=source_scheduler_service,
        ingestion_repository=ingestion_repository,
        ingestion_service=ingestion_service,
        ingestion_lease_repository=ingestion_lease_repository,
        ingestion_lease_service=ingestion_lease_service,
        ingestion_worker_registry=ingestion_worker_registry,
        ingestion_worker_observer=ingestion_worker_observer,
        ingestion_worker_runner=ingestion_worker_runner,
        content_supply_cycle_repository=content_supply_cycle_repository,
        content_supply_cycle_observer=content_supply_cycle_observer,
        content_supply_cycle_service=content_supply_cycle_service,
        content_supply_health_repository=content_supply_health_repository,
        content_supply_health_service=content_supply_health_service,
        proposal_queue_repository=proposal_queue_repository,
        projection_repository=projection_repository,
        projection_service=projection_service,
        secured_projection_service=SecuredEditorialProjectionService(
            projection=projection_service,
            security=admin_security_service,
        ),
    )
