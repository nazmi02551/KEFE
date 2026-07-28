from __future__ import annotations

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.postgres_admin_security import PostgresAdminSessionStore
from kefe_api.infrastructure.postgres_content_authoring import PostgresContentAuthoringRepository
from kefe_api.infrastructure.postgres_context import PostgresContextRepository
from kefe_api.infrastructure.postgres_identity import PostgresIdentityRepository
from kefe_api.infrastructure.postgres_perspective_decision import (
    PostgresPerspectiveDecisionRepository,
)
from kefe_api.infrastructure.postgres_progress import PostgresProgressRepository
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.ports import AdminSessionStore
from kefe_api.modules.content_authoring.in_memory import InMemoryContentAuthoringRepository
from kefe_api.modules.content_authoring.ports import ContentAuthoringRepository
from kefe_api.modules.context.bootstrap import build_demo_context_repository
from kefe_api.modules.context.ports import ContextRepository
from kefe_api.modules.decision.bootstrap import build_demo_repository
from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.decision.ports import DecisionRepository
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
from kefe_api.modules.identity.ports import IdentityRepository
from kefe_api.modules.progress.in_memory import InMemoryProgressRepository
from kefe_api.modules.progress.ports import ProgressRepository


def build_decision_repository(settings: Settings) -> DecisionRepository:
    if settings.persistence_backend == "memory":
        return build_demo_repository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresPerspectiveDecisionRepository(build_engine(settings.database_url))


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
        if not isinstance(decision_repository, InMemoryDecisionRepository):
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


def build_content_authoring_repository(settings: Settings) -> ContentAuthoringRepository:
    if settings.persistence_backend == "memory":
        return InMemoryContentAuthoringRepository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresContentAuthoringRepository(build_engine(settings.database_url))


def build_admin_session_store(settings: Settings) -> AdminSessionStore:
    if settings.persistence_backend == "memory":
        return InMemoryAdminSessionStore()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresAdminSessionStore(build_engine(settings.database_url))
