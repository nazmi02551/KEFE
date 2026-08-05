from __future__ import annotations

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.postgres_account_continuity import PostgresAccountContinuityRepository
from kefe_api.infrastructure.postgres_admin_security import PostgresAdminSessionStore
from kefe_api.infrastructure.postgres_case_media import PostgresCaseMediaRepository
from kefe_api.infrastructure.postgres_community_reason import PostgresCommunityReasonRepository
from kefe_api.infrastructure.postgres_consensus import PostgresConsensusRepository
from kefe_api.infrastructure.postgres_content_configuration import (
    PostgresContentConfigurationRepository,
)
from kefe_api.infrastructure.postgres_context import PostgresContextRepository
from kefe_api.infrastructure.postgres_flow_pinned_content_authoring import (
    PostgresFlowPinnedContentAuthoringRepository,
)
from kefe_api.infrastructure.postgres_identity import PostgresIdentityRepository
from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.infrastructure.postgres_otp_request_guard import (
    GuardedPostgresAccountContinuityRepository,
)
from kefe_api.infrastructure.postgres_privacy import PostgresPrivacyRepository
from kefe_api.infrastructure.postgres_progress import PostgresProgressRepository
from kefe_api.infrastructure.postgres_reflection_decision import (
    PostgresReflectionDecisionRepository,
)
from kefe_api.infrastructure.postgres_sharing import PostgresShareRepository
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.ports import AdminSessionStore
from kefe_api.modules.case_media.in_memory import InMemoryCaseMediaRepository
from kefe_api.modules.case_media.ports import CaseMediaRepository
from kefe_api.modules.community_reason.in_memory import InMemoryCommunityReasonRepository
from kefe_api.modules.community_reason.ports import CommunityReasonRepository
from kefe_api.modules.consensus.in_memory import build_demo_consensus_repository
from kefe_api.modules.consensus.ports import ConsensusRepository
from kefe_api.modules.content_authoring.in_memory import InMemoryContentAuthoringRepository
from kefe_api.modules.content_authoring.ports import ContentAuthoringRepository
from kefe_api.modules.content_configuration.bootstrap import build_default_content_configuration
from kefe_api.modules.content_configuration.in_memory import (
    InMemoryContentConfigurationRepository,
)
from kefe_api.modules.content_configuration.ports import ContentConfigurationRepository
from kefe_api.modules.context.bootstrap import build_demo_context_repository
from kefe_api.modules.context.ports import ContextRepository
from kefe_api.modules.decision.bootstrap import build_demo_repository
from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.decision.lineage_in_memory import InMemoryLineageDecisionRepository
from kefe_api.modules.decision.ports import DecisionRepository
from kefe_api.modules.editorial_projection.ingestion_source import (
    IngestionReviewedProposalSource,
)
from kefe_api.modules.editorial_projection.ports import ReviewedProposalSource
from kefe_api.modules.identity.account_in_memory import InMemoryAccountContinuityRepository
from kefe_api.modules.identity.account_ports import AccountContinuityRepository
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
from kefe_api.modules.identity.otp_request_guard import (
    GuardedInMemoryAccountContinuityRepository,
    OtpRequestAbusePolicy,
)
from kefe_api.modules.identity.ports import IdentityRepository
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.ports import KnowledgeRepository
from kefe_api.modules.privacy.in_memory import InMemoryPrivacyRepository
from kefe_api.modules.privacy.ports import PrivacyRepository
from kefe_api.modules.progress.in_memory import InMemoryProgressRepository
from kefe_api.modules.progress.ports import ProgressRepository
from kefe_api.modules.sharing.in_memory import InMemoryShareRepository
from kefe_api.modules.sharing.ports import ShareRepository


def build_decision_repository(settings: Settings) -> DecisionRepository:
    if settings.persistence_backend == "memory":
        return build_demo_repository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresReflectionDecisionRepository(build_engine(settings.database_url))


def build_consensus_repository(settings: Settings) -> ConsensusRepository:
    if settings.persistence_backend == "memory":
        return build_demo_consensus_repository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresConsensusRepository(build_engine(settings.database_url))


def build_context_repository(settings: Settings) -> ContextRepository:
    if settings.persistence_backend == "memory":
        return build_demo_context_repository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresContextRepository(build_engine(settings.database_url))


def build_progress_repository(
    settings: Settings,
    decision_repository: DecisionRepository,
) -> ProgressRepository:
    if settings.persistence_backend == "memory":
        if not isinstance(decision_repository, InMemoryLineageDecisionRepository):
            raise RuntimeError("memory progress requires the in-memory decision repository")
        return InMemoryProgressRepository(decision_repository)

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresProgressRepository(build_engine(settings.database_url))


def build_identity_repository(settings: Settings) -> IdentityRepository:
    if settings.persistence_backend == "memory":
        return InMemoryIdentityRepository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresIdentityRepository(build_engine(settings.database_url))


def _otp_request_abuse_policy(settings: Settings) -> OtpRequestAbusePolicy:
    return OtpRequestAbusePolicy.from_seconds(
        cooldown_seconds=settings.otp_request_cooldown_seconds,
        window_seconds=settings.otp_request_window_seconds,
        window_limit=settings.otp_request_window_limit,
        retention_seconds=settings.otp_request_guard_retention_seconds,
    )


def _otp_request_guard_enabled(settings: Settings) -> bool:
    mode = settings.otp_request_guard_mode
    production = settings.environment.strip().lower() == "production"
    if production and mode == "OFF":
        raise RuntimeError(
            "production forbids KEFE_OTP_REQUEST_GUARD_MODE=OFF"
        )
    return mode == "ENFORCE" or (mode == "AUTO" and production)


def build_account_continuity_repository(
    settings: Settings,
    identity_repository: IdentityRepository,
) -> AccountContinuityRepository:
    guard_enabled = _otp_request_guard_enabled(settings)
    policy = _otp_request_abuse_policy(settings) if guard_enabled else None
    if settings.persistence_backend == "memory":
        if not isinstance(identity_repository, InMemoryIdentityRepository):
            raise RuntimeError("memory account continuity requires in-memory identity")
        if policy is not None:
            return GuardedInMemoryAccountContinuityRepository(
                identity_repository,
                policy,
            )
        return InMemoryAccountContinuityRepository(identity_repository)
    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")
    engine = build_engine(settings.database_url)
    if policy is not None:
        return GuardedPostgresAccountContinuityRepository(engine, policy)
    return PostgresAccountContinuityRepository(engine)


def build_share_repository(settings: Settings) -> ShareRepository:
    if settings.persistence_backend == "memory":
        return InMemoryShareRepository()
    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")
    return PostgresShareRepository(build_engine(settings.database_url))


def build_community_reason_repository(settings: Settings) -> CommunityReasonRepository:
    if settings.persistence_backend == "memory":
        return InMemoryCommunityReasonRepository()
    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")
    return PostgresCommunityReasonRepository(build_engine(settings.database_url))


def build_privacy_repository(
    settings: Settings,
    decision_repository: DecisionRepository,
    identity_repository: IdentityRepository,
) -> PrivacyRepository:
    if settings.persistence_backend == "memory":
        if not isinstance(decision_repository, InMemoryDecisionRepository):
            raise RuntimeError("memory privacy requires in-memory decision repository")
        if not isinstance(identity_repository, InMemoryIdentityRepository):
            raise RuntimeError("memory privacy requires in-memory identity repository")
        return InMemoryPrivacyRepository(
            decision_repository=decision_repository,
            identity_repository=identity_repository,
        )
    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")
    return PostgresPrivacyRepository(build_engine(settings.database_url))


def build_content_authoring_repository(settings: Settings) -> ContentAuthoringRepository:
    if settings.persistence_backend == "memory":
        return InMemoryContentAuthoringRepository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresFlowPinnedContentAuthoringRepository(build_engine(settings.database_url))


def build_case_media_repository(settings: Settings) -> CaseMediaRepository:
    if settings.persistence_backend == "memory":
        return InMemoryCaseMediaRepository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresCaseMediaRepository(build_engine(settings.database_url))


def build_content_configuration_repository(
    settings: Settings,
) -> ContentConfigurationRepository:
    seed = build_default_content_configuration()
    if settings.persistence_backend == "memory":
        return InMemoryContentConfigurationRepository(seed)

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    repository = PostgresContentConfigurationRepository(build_engine(settings.database_url))
    repository.seed_if_empty(seed)
    return repository


def build_knowledge_repository(settings: Settings) -> KnowledgeRepository:
    if settings.persistence_backend == "memory":
        return InMemoryKnowledgeRepository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresKnowledgeRepository(build_engine(settings.database_url))


def build_ingestion_orchestration_repository(
    settings: Settings,
) -> IngestionOrchestrationRepository:
    if settings.persistence_backend == "memory":
        return InMemoryIngestionOrchestrationRepository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresIngestionOrchestrationRepository(build_engine(settings.database_url))


def build_reviewed_proposal_source(
    repository: IngestionOrchestrationRepository,
) -> ReviewedProposalSource:
    return IngestionReviewedProposalSource(repository)


def build_admin_session_store(settings: Settings) -> AdminSessionStore:
    if settings.persistence_backend == "memory":
        return InMemoryAdminSessionStore()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresAdminSessionStore(build_engine(settings.database_url))
