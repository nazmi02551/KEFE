from fastapi import FastAPI

from kefe_api.core.exception_handlers import install_exception_handlers
from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.editorial_pipeline import build_editorial_pipeline
from kefe_api.infrastructure.persistence import (
    build_account_continuity_repository,
    build_admin_session_store,
    build_community_reason_repository,
    build_consensus_repository,
    build_content_authoring_repository,
    build_content_configuration_repository,
    build_context_repository,
    build_decision_repository,
    build_identity_repository,
    build_privacy_repository,
    build_progress_repository,
    build_share_repository,
)
from kefe_api.modules.admin_security.content_authoring import SecuredContentAuthoringService
from kefe_api.modules.admin_security.content_configuration import (
    SecuredContentConfigurationService,
)
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.router import router as admin_router
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.community_reason.admin_router import router as community_reason_admin_router
from kefe_api.modules.community_reason.router import router as community_reason_router
from kefe_api.modules.community_reason.service import CommunityReasonService
from kefe_api.modules.consensus.router import router as consensus_router
from kefe_api.modules.consensus.service import ConsensusService
from kefe_api.modules.content_authoring.registry import default_authoring_registry
from kefe_api.modules.content_authoring.service import ContentAuthoringService
from kefe_api.modules.content_configuration.admin_router import (
    router as admin_content_configuration_router,
)
from kefe_api.modules.content_configuration.publication_resolver import (
    ContentConfigurationPublicationResolver,
)
from kefe_api.modules.content_configuration.service import ContentConfigurationService
from kefe_api.modules.context.router import router as context_router
from kefe_api.modules.context.service import ContextService
from kefe_api.modules.decision.lineage_aware_service import LineageAwareDecisionService
from kefe_api.modules.decision.lineage_router import router as decision_lineage_router
from kefe_api.modules.decision.lineage_service import DecisionLineageService
from kefe_api.modules.decision.reflection_router import router as reflection_router
from kefe_api.modules.decision.reflection_service import ReflectionService
from kefe_api.modules.decision.router import router as decision_router
from kefe_api.modules.flow_runtime.router import router as flow_runtime_router
from kefe_api.modules.flow_runtime.service import FlowRuntimeService
from kefe_api.modules.global_discovery.router import router as global_discovery_router
from kefe_api.modules.global_discovery.service import GlobalDiscoveryService
from kefe_api.modules.health.router import router as health_router
from kefe_api.modules.identity.account_router import router as account_router
from kefe_api.modules.identity.account_service import AccountContinuityService
from kefe_api.modules.identity.admission import (
    GuestAdmissionGuard,
    InMemoryGuestIssueRateLimiter,
    IntegrityMode,
    UnconfiguredDeviceIntegrityVerifier,
)
from kefe_api.modules.identity.otp_delivery import CapturingOtpDelivery, DisabledOtpDelivery
from kefe_api.modules.identity.router import router as identity_router
from kefe_api.modules.identity.service import IdentityService
from kefe_api.modules.privacy.router import router as privacy_router
from kefe_api.modules.privacy.service import PrivacyService
from kefe_api.modules.progress.router import router as progress_router
from kefe_api.modules.progress.service import ProgressService
from kefe_api.modules.sharing.router import router as sharing_router
from kefe_api.modules.sharing.service import ShareService


def _api_at_least(version: str, major: int, minor: int) -> bool:
    try:
        parts = version.split(".")
        return (int(parts[0]), int(parts[1])) >= (major, minor)
    except (ValueError, IndexError):
        return False


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.api_title, version=settings.api_version)

    context_repository = build_context_repository(settings)
    decision_repository = build_decision_repository(settings)
    consensus_repository = build_consensus_repository(settings)
    identity_repository = build_identity_repository(settings)
    account_continuity_repository = build_account_continuity_repository(
        settings,
        identity_repository,
    )
    progress_repository = build_progress_repository(settings, decision_repository)
    share_repository = build_share_repository(settings)
    community_reason_repository = build_community_reason_repository(settings)
    privacy_repository = build_privacy_repository(
        settings,
        decision_repository,
        identity_repository,
    )
    content_authoring_repository = build_content_authoring_repository(settings)
    content_configuration_repository = build_content_configuration_repository(settings)
    admin_session_store = build_admin_session_store(settings)

    admin_security_service = AdminSecurityService(
        session_resolver=admin_session_store,
        policy=default_admin_security_policy(),
    )
    content_authoring_service = ContentAuthoringService(
        content_authoring_repository,
        default_authoring_registry(),
        ContentConfigurationPublicationResolver(content_configuration_repository),
    )
    secured_content_authoring_service = SecuredContentAuthoringService(
        authoring=content_authoring_service,
        repository=content_authoring_repository,
        security=admin_security_service,
    )
    editorial_pipeline = build_editorial_pipeline(
        settings,
        content_authoring_repository=content_authoring_repository,
        admin_security_service=admin_security_service,
    )
    content_configuration_service = ContentConfigurationService(
        repository=content_configuration_repository,
        security=admin_security_service,
    )
    secured_content_configuration_service = SecuredContentConfigurationService(
        configuration=content_configuration_service,
        repository=content_configuration_repository,
        security=admin_security_service,
    )
    flow_runtime_service = FlowRuntimeService(decision_repository)
    otp_delivery = (
        DisabledOtpDelivery()
        if settings.environment.lower() == "production"
        else CapturingOtpDelivery()
    )

    app.state.context_repository = context_repository
    app.state.context_service = ContextService(context_repository)
    app.state.decision_repository = decision_repository
    app.state.decision_service = LineageAwareDecisionService(decision_repository)
    app.state.global_discovery_service = GlobalDiscoveryService(decision_repository)
    app.state.consensus_repository = consensus_repository
    app.state.consensus_service = ConsensusService(
        consensus_repository=consensus_repository,
        decision_repository=decision_repository,
    )
    app.state.flow_runtime_service = flow_runtime_service
    app.state.decision_lineage_service = DecisionLineageService(
        decision_repository,
        flow_runtime_service,
    )
    app.state.reflection_service = ReflectionService(
        decision_repository,
        flow_runtime_service,
    )
    app.state.identity_repository = identity_repository
    app.state.identity_service = IdentityService(
        repository=identity_repository,
        guest_token_ttl_days=settings.guest_token_ttl_days,
    )
    app.state.otp_delivery = otp_delivery
    app.state.account_continuity_repository = account_continuity_repository
    app.state.account_continuity_service = AccountContinuityService(
        repository=account_continuity_repository,
        delivery=otp_delivery,
        challenge_ttl_minutes=settings.otp_challenge_ttl_minutes,
        verification_ttl_minutes=settings.otp_verification_ttl_minutes,
        account_token_ttl_days=settings.account_token_ttl_days,
        max_attempts=settings.otp_max_attempts,
    )
    app.state.progress_repository = progress_repository
    app.state.progress_service = ProgressService(progress_repository)
    app.state.share_repository = share_repository
    app.state.share_service = ShareService(
        repository=share_repository,
        decision_repository=decision_repository,
        ttl_days=settings.share_ttl_days,
    )
    app.state.community_reason_repository = community_reason_repository
    app.state.community_reason_service = CommunityReasonService(
        repository=community_reason_repository,
        decision_repository=decision_repository,
    )
    app.state.privacy_repository = privacy_repository
    app.state.privacy_service = PrivacyService(privacy_repository)
    app.state.content_authoring_repository = content_authoring_repository
    app.state.content_authoring_service = content_authoring_service
    app.state.ingestion_orchestration_repository = (
        editorial_pipeline.ingestion_repository
    )
    app.state.ingestion_orchestration_service = editorial_pipeline.ingestion_service
    app.state.editorial_projection_repository = (
        editorial_pipeline.projection_repository
    )
    app.state.editorial_projection_service = editorial_pipeline.projection_service
    app.state.secured_editorial_projection_service = (
        editorial_pipeline.secured_projection_service
    )
    app.state.content_configuration_repository = content_configuration_repository
    app.state.content_configuration_service = content_configuration_service
    app.state.admin_session_store = admin_session_store
    app.state.admin_csrf_verifier = admin_session_store
    app.state.admin_security_service = admin_security_service
    app.state.secured_content_authoring_service = secured_content_authoring_service
    app.state.secured_content_configuration_service = secured_content_configuration_service
    app.state.guest_admission_guard = GuestAdmissionGuard(
        limiter=InMemoryGuestIssueRateLimiter(),
        integrity_verifier=UnconfiguredDeviceIntegrityVerifier(),
        rate_limit=settings.guest_issue_rate_limit,
        rate_window_seconds=settings.guest_issue_rate_window_seconds,
        integrity_mode=IntegrityMode(settings.device_integrity_mode),
    )

    install_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(identity_router)
    app.include_router(account_router)
    app.include_router(context_router)
    app.include_router(decision_router)
    if _api_at_least(settings.api_version, 0, 20):
        app.include_router(global_discovery_router)
    app.include_router(consensus_router)
    app.include_router(community_reason_router)
    app.include_router(sharing_router)
    app.include_router(privacy_router)
    app.include_router(decision_lineage_router)
    app.include_router(reflection_router)
    app.include_router(flow_runtime_router)
    app.include_router(progress_router)
    app.include_router(admin_router)
    app.include_router(admin_content_configuration_router)
    app.include_router(community_reason_admin_router)
    return app


app = create_app()
