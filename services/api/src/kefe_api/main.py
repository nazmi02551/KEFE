from fastapi import FastAPI

from kefe_api.core.exception_handlers import install_exception_handlers
from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.persistence import (
    build_context_repository,
    build_decision_repository,
    build_identity_repository,
    build_progress_repository,
)
from kefe_api.modules.context.router import router as context_router
from kefe_api.modules.context.service import ContextService
from kefe_api.modules.decision.router import router as decision_router
from kefe_api.modules.decision.service import DecisionService
from kefe_api.modules.health.router import router as health_router
from kefe_api.modules.identity.admission import (
    GuestAdmissionGuard,
    InMemoryGuestIssueRateLimiter,
    IntegrityMode,
    UnconfiguredDeviceIntegrityVerifier,
)
from kefe_api.modules.identity.router import router as identity_router
from kefe_api.modules.identity.service import IdentityService
from kefe_api.modules.progress.router import router as progress_router
from kefe_api.modules.progress.service import ProgressService


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.api_title, version=settings.api_version)

    context_repository = build_context_repository(settings)
    decision_repository = build_decision_repository(settings)
    identity_repository = build_identity_repository(settings)
    progress_repository = build_progress_repository(settings, decision_repository)

    app.state.context_repository = context_repository
    app.state.context_service = ContextService(context_repository)
    app.state.decision_repository = decision_repository
    app.state.decision_service = DecisionService(decision_repository)
    app.state.identity_repository = identity_repository
    app.state.identity_service = IdentityService(
        repository=identity_repository,
        guest_token_ttl_days=settings.guest_token_ttl_days,
    )
    app.state.progress_repository = progress_repository
    app.state.progress_service = ProgressService(progress_repository)
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
    app.include_router(context_router)
    app.include_router(decision_router)
    app.include_router(progress_router)
    return app


app = create_app()
