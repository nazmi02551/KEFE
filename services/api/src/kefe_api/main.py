from fastapi import FastAPI

from kefe_api.core.exception_handlers import install_exception_handlers
from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.persistence import (
    build_decision_repository,
    build_identity_repository,
)
from kefe_api.modules.decision.router import router as decision_router
from kefe_api.modules.decision.service import DecisionService
from kefe_api.modules.health.router import router as health_router
from kefe_api.modules.identity.router import router as identity_router
from kefe_api.modules.identity.service import IdentityService


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.api_title, version=settings.api_version)

    decision_repository = build_decision_repository(settings)
    identity_repository = build_identity_repository(settings)

    app.state.decision_repository = decision_repository
    app.state.decision_service = DecisionService(decision_repository)
    app.state.identity_repository = identity_repository
    app.state.identity_service = IdentityService(
        repository=identity_repository,
        guest_token_ttl_days=settings.guest_token_ttl_days,
    )

    install_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(identity_router)
    app.include_router(decision_router)
    return app


app = create_app()
