from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import text

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine

ReadinessProbe = Callable[[], None]


def build_readiness_probe(settings: Settings) -> ReadinessProbe:
    """Build a minimal dependency probe without exposing provider details."""

    if settings.persistence_backend == "memory":
        return lambda: None

    if not settings.database_url:
        raise RuntimeError("PostgreSQL readiness requires a database URL")

    engine = build_engine(settings.database_url)

    def probe() -> None:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    return probe
