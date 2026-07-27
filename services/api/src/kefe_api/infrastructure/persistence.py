from __future__ import annotations

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.postgres_decision import PostgresDecisionRepository
from kefe_api.modules.decision.bootstrap import build_demo_repository
from kefe_api.modules.decision.ports import DecisionRepository


def build_decision_repository(settings: Settings) -> DecisionRepository:
    if settings.persistence_backend == "memory":
        return build_demo_repository()

    if not settings.database_url:
        raise RuntimeError("KEFE_DATABASE_URL is required when persistence_backend=postgres")

    return PostgresDecisionRepository(build_engine(settings.database_url))
