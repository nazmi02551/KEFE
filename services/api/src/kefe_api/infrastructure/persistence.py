from __future__ import annotations

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.postgres_explore_decision import PostgresExploreDecisionRepository
from kefe_api.infrastructure.postgres_identity import PostgresIdentityRepository
from kefe_api.modules.decision.bootstrap import build_demo_repository
from kefe_api.modules.decision.ports import DecisionRepository
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
from kefe_api.modules.identity.ports import IdentityRepository


def build_decision_repository(settings: Settings) -> DecisionRepository:
    if settings.persistence_backend == "memory":
        return build_demo_repository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresExploreDecisionRepository(build_engine(settings.database_url))


def build_identity_repository(settings: Settings) -> IdentityRepository:
    if settings.persistence_backend == "memory":
        return InMemoryIdentityRepository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresIdentityRepository(build_engine(settings.database_url))
