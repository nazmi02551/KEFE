from __future__ import annotations

from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.admin_runtime import AdminRuntime, build_admin_runtime
from kefe_api.modules.admin_http.app import create_admin_app


def create_app() -> tuple[object, AdminRuntime]:
    settings = get_settings()
    runtime = build_admin_runtime(settings)
    app = create_admin_app(
        security=runtime.security,
        csrf_verifier=runtime.session_store,
        authoring=runtime.secured_authoring,
    )
    app.state.admin_runtime = runtime
    return app, runtime


app, runtime = create_app()
