from __future__ import annotations

from kefe_api.core.settings import Settings
from kefe_api.infrastructure.db import build_engine
from kefe_api.infrastructure.postgres_public_feed_manual_capture import (
    PostgresPublicFeedManualCaptureAuditRepository,
)
from kefe_api.modules.knowledge.public_feed_manual_capture import (
    InMemoryPublicFeedManualCaptureAuditRepository,
    PublicFeedManualCaptureAuditRepository,
)


def build_public_feed_manual_capture_audit_repository(
    settings: Settings,
) -> PublicFeedManualCaptureAuditRepository:
    if settings.persistence_backend == "memory":
        return InMemoryPublicFeedManualCaptureAuditRepository()
    if not settings.database_url:
        raise RuntimeError(
            "KEFE_DATABASE_URL is required when persistence_backend=postgres"
        )
    return PostgresPublicFeedManualCaptureAuditRepository(
        build_engine(settings.database_url)
    )


__all__ = ["build_public_feed_manual_capture_audit_repository"]
