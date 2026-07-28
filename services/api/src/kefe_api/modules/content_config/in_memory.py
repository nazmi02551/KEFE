from __future__ import annotations

from threading import RLock
from uuid import UUID

from kefe_api.modules.content_config.models import (
    ContentConfigLifecycle,
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
)


class InMemoryContentConfigurationRepository:
    def __init__(self, seed: ContentConfigurationSnapshot | None = None) -> None:
        self._lock = RLock()
        self._snapshots: dict[UUID, ContentConfigurationSnapshot] = {}
        self._audit: list[ContentConfigurationAuditEntry] = []
        if seed is not None:
            self._snapshots[seed.id] = seed

    def current_published(self) -> ContentConfigurationSnapshot | None:
        with self._lock:
            published = [
                snapshot
                for snapshot in self._snapshots.values()
                if snapshot.state is ContentConfigLifecycle.PUBLISHED
            ]
            if not published:
                return None
            return max(published, key=lambda item: item.version_no)

    def get_snapshot(self, snapshot_id: UUID) -> ContentConfigurationSnapshot | None:
        with self._lock:
            return self._snapshots.get(snapshot_id)

    def next_version_no(self) -> int:
        with self._lock:
            return max((item.version_no for item in self._snapshots.values()), default=0) + 1

    def save_draft(self, snapshot: ContentConfigurationSnapshot) -> None:
        with self._lock:
            current = self._snapshots.get(snapshot.id)
            if current is not None and current.state is not ContentConfigLifecycle.DRAFT:
                raise ValueError("published content configuration is immutable")
            if snapshot.state is not ContentConfigLifecycle.DRAFT:
                raise ValueError("save_draft accepts only DRAFT snapshots")
            self._snapshots[snapshot.id] = snapshot

    def publish_atomically(
        self,
        *,
        snapshot: ContentConfigurationSnapshot,
        audit: ContentConfigurationAuditEntry,
    ) -> tuple[ContentConfigurationSnapshot, ContentConfigurationSnapshot | None]:
        with self._lock:
            current = self._snapshots.get(snapshot.id)
            if current is None or current.state is not ContentConfigLifecycle.DRAFT:
                raise ValueError("configuration lifecycle changed concurrently")

            previous = self.current_published()
            if previous is not None:
                self._snapshots[previous.id] = previous.with_state(
                    ContentConfigLifecycle.SUPERSEDED,
                    published_at=previous.published_at,
                )
            self._snapshots[snapshot.id] = snapshot
            self._audit.append(audit)
            return snapshot, previous

    def list_audit(self) -> tuple[ContentConfigurationAuditEntry, ...]:
        with self._lock:
            return tuple(self._audit)
