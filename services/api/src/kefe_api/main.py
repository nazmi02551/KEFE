from fastapi import FastAPI

from kefe_api.core.settings import get_settings
from kefe_api.modules.health.router import router as health_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.api_title, version=settings.api_version)
    app.include_router(health_router)
    return app


app = create_app()
