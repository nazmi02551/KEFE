from __future__ import annotations

from fastapi import FastAPI, Request
from starlette.responses import Response

from kefe_api.core.exception_handlers import install_exception_handlers
from kefe_api.modules.admin_http.router import router
from kefe_api.modules.admin_security.content_authoring import SecuredContentAuthoringService
from kefe_api.modules.admin_security.ports import AdminCsrfVerifier
from kefe_api.modules.admin_security.service import AdminSecurityService


def create_admin_app(
    *,
    security: AdminSecurityService,
    csrf_verifier: AdminCsrfVerifier,
    authoring: SecuredContentAuthoringService,
) -> FastAPI:
    app = FastAPI(
        title="KEFE Admin API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.admin_security_service = security
    app.state.admin_csrf_verifier = csrf_verifier
    app.state.secured_content_authoring = authoring

    install_exception_handlers(app)

    @app.middleware("http")
    async def admin_no_store(request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    app.include_router(router)
    return app
