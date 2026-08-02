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
from kefe_api.infrastructure.postgres_source_acquisition_scheduler import (
    PostgresSourceAcquisitionSchedulerRepository,
)
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
from kefe_api.modules.knowledge.source_acquisition import (
    InMemorySourceCaptureRegistry,
    NoOpSourceAcquisitionObserver,
    SourceAcquisitionObserver,
    SourceAcquisitionService,
    SourceCaptureRegistry,
)
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
    source_acquisition_observer: SourceAcquisitionObserver = (
        NoOpSourceAcquisitionObserver()
    )
    source_acquisition_service = SourceAcquisitionService(
        knowledge_repository=knowledge_repository,
        ingestion_service=ingestion_service,
        registry=source_capture_registry,
        observer=source_acquisition_observer,
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
