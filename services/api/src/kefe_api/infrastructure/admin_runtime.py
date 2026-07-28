from __future__ import annotations

from dataclasses import dataclass

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.postgres_admin_security import PostgresAdminSessionStore
from kefe_api.infrastructure.postgres_content_authoring import PostgresContentAuthoringRepository
from kefe_api.modules.admin_security.content_authoring import SecuredContentAuthoringService
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.ports import AdminSessionStore
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_authoring.in_memory import InMemoryContentAuthoringRepository
from kefe_api.modules.content_authoring.ports import ContentAuthoringRepository
from kefe_api.modules.content_authoring.registry import default_authoring_registry
from kefe_api.modules.content_authoring.service import ContentAuthoringService


@dataclass(slots=True)
class AdminRuntime:
    session_store: AdminSessionStore
    authoring_repository: ContentAuthoringRepository
    security: AdminSecurityService
    secured_authoring: SecuredContentAuthoringService


def build_admin_runtime(settings: Settings) -> AdminRuntime:
    if settings.persistence_backend == "memory":
        session_store: AdminSessionStore = InMemoryAdminSessionStore()
        authoring_repository: ContentAuthoringRepository = InMemoryContentAuthoringRepository()
    else:
        if not settings.database_url:
            raise RuntimeError(
                "KEFE_DATABASE_URL is required when persistence_backend=postgres"
            )
        engine = build_engine(settings.database_url)
        session_store = PostgresAdminSessionStore(engine)
        authoring_repository = PostgresContentAuthoringRepository(engine)

    security = AdminSecurityService(
        session_resolver=session_store,
        policy=default_admin_security_policy(),
    )
    authoring = ContentAuthoringService(
        authoring_repository,
        default_authoring_registry(),
    )
    secured = SecuredContentAuthoringService(
        authoring=authoring,
        repository=authoring_repository,
        security=security,
    )
    return AdminRuntime(
        session_store=session_store,
        authoring_repository=authoring_repository,
        security=security,
        secured_authoring=secured,
    )
