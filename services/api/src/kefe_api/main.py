from fastapi import FastAPI

from kefe_api.core.exception_handlers import install_exception_handlers
from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.persistence import build_decision_repository
from kefe_api.modules.decision.router import router as decision_router
from kefe_api.modules.decision.service import DecisionService
from kefe_api.modules.health.router import router as health_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.api_title, version=settings.api_version)

    repository = build_decision_repository(settings)
    app.state.decision_repository = repository
    app.state.decision_service = DecisionService(repository)

    install_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(decision_router)
    return app


app = create_app()
