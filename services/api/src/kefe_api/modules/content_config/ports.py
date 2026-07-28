from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.content_config.models import (
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
)


class ContentConfigurationRepository(Protocol):
    def current_published(self) -> ContentConfigurationSnapshot | None: ...

    def get_snapshot(self, snapshot_id: UUID) -> ContentConfigurationSnapshot | None: ...

    def next_version_no(self) -> int: ...

    def save_draft(self, snapshot: ContentConfigurationSnapshot) -> None: ...

    def publish_atomically(
        self,
        *,
        snapshot: ContentConfigurationSnapshot,
        audit: ContentConfigurationAuditEntry,
    ) -> tuple[ContentConfigurationSnapshot, ContentConfigurationSnapshot | None]: ...

    def list_audit(self) -> tuple[ContentConfigurationAuditEntry, ...]: ...
