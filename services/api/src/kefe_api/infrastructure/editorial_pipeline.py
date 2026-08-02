from __future__ import annotations

from dataclasses import dataclass

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.postgres_editorial_projection import (
    PostgresEditorialProjectionRepository,
)
from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_ingestion_run_leases import (
    PostgresIngestionRunLeaseRepository,
)
from kefe_api.infrastructure.postgres_proposal_review_queue import (
    PostgresProposalReviewQueueRepository,
)
from kefe_api.modules.admin_security.editorial_projection import (
    SecuredEditorialProjectionService,
)
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_authoring.in_memory import (
    InMemoryContentAuthoringRepository,
)
from kefe_api.modules.content_authoring.ports import ContentAuthoringRepository
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
    InMemoryIngestionWorkerRuntimeRegistry,
    IngestionWorkerObserver,
    IngestionWorkerRuntimeRegistry,
    NoOpIngestionWorkerObserver,
)
from kefe_api.modules.ingestion_orchestration.worker_service import (
    IngestionWorkerRunner,
)


@dataclass(frozen=True, slots=True)
class EditorialPipeline:
    ingestion_repository: IngestionOrchestrationRepository
    ingestion_service: IngestionOrchestrationService
    ingestion_lease_repository: IngestionRunLeaseRepository
    ingestion_lease_service: IngestionRunLeaseService
    ingestion_worker_registry: IngestionWorkerRuntimeRegistry
    ingestion_worker_observer: IngestionWorkerObserver
    ingestion_worker_runner: IngestionWorkerRunner
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
        memory_ingestion = InMemoryIngestionOrchestrationRepository()
        ingestion_repository: IngestionOrchestrationRepository = memory_ingestion
        ingestion_lease_repository: IngestionRunLeaseRepository = (
            InMemoryIngestionRunLeaseRepository(memory_ingestion)
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
        ingestion_repository = PostgresIngestionOrchestrationRepository(engine)
        ingestion_lease_repository = PostgresIngestionRunLeaseRepository(engine)
        proposal_queue_repository = PostgresProposalReviewQueueRepository(engine)
        projection_repository = PostgresEditorialProjectionRepository(engine)

    ingestion_service = IngestionOrchestrationService(ingestion_repository)
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
        ingestion_repository=ingestion_repository,
        ingestion_service=ingestion_service,
        ingestion_lease_repository=ingestion_lease_repository,
        ingestion_lease_service=ingestion_lease_service,
        ingestion_worker_registry=ingestion_worker_registry,
        ingestion_worker_observer=ingestion_worker_observer,
        ingestion_worker_runner=ingestion_worker_runner,
        proposal_queue_repository=proposal_queue_repository,
        projection_repository=projection_repository,
        projection_service=projection_service,
        secured_projection_service=SecuredEditorialProjectionService(
            projection=projection_service,
            security=admin_security_service,
        ),
    )
