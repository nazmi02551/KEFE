from __future__ import annotations

from copy import deepcopy
from threading import RLock
from uuid import UUID

from kefe_api.modules.content_configuration.models import (
    ContentConfigLifecycle,
    ContentConfigurationAuditEntry,
    ContentConfigurationSnapshot,
)


class InMemoryContentConfigurationRepository:
    def __init__(self, seed: ContentConfigurationSnapshot | None = None) -> None:
        self._lock = RLock()
        self._versions: dict[UUID, ContentConfigurationSnapshot] = {}
        self._audit: list[ContentConfigurationAuditEntry] = []
        if seed is not None:
            self._versions[seed.id] = deepcopy(seed)

    def current_published(self) -> ContentConfigurationSnapshot | None:
        with self._lock:
            published = [
                item for item in self._versions.values() if item.state is ContentConfigLifecycle.PUBLISHED
            ]
            if not published:
                return None
            return deepcopy(max(published, key=lambda item: item.version_no))

    def get(self, version_id: UUID) -> ContentConfigurationSnapshot | None:
        with self._lock:
            item = self._versions.get(version_id)
            return deepcopy(item) if item is not None else None

    def list_versions(self) -> tuple[ContentConfigurationSnapshot, ...]:
        with self._lock:
            return tuple(
                deepcopy(item)
                for item in sorted(self._versions.values(), key=lambda item: item.version_no)
            )

    def next_version_no(self) -> int:
        with self._lock:
            return 1 + max((item.version_no for item in self._versions.values()), default=0)

    def save_draft(
        self,
        snapshot: ContentConfigurationSnapshot,
        *,
        audit: ContentConfigurationAuditEntry,
    ) -> None:
        with self._lock:
            if snapshot.id in self._versions:
                raise ValueError("content configuration version already exists")
            self._versions[snapshot.id] = deepcopy(snapshot)
            self._audit.append(deepcopy(audit))

    def replace_draft(
        self,
        snapshot: ContentConfigurationSnapshot,
        *,
        audit: ContentConfigurationAuditEntry,
    ) -> None:
        with self._lock:
            current = self._versions.get(snapshot.id)
            if current is None:
                raise KeyError(snapshot.id)
            if current.state is not ContentConfigLifecycle.DRAFT:
                raise ValueError("only DRAFT content configuration may be replaced")
            self._versions[snapshot.id] = deepcopy(snapshot)
            self._audit.append(deepcopy(audit))

    def publish_atomically(
        self,
        *,
        snapshot: ContentConfigurationSnapshot,
        audit: ContentConfigurationAuditEntry,
    ) -> tuple[ContentConfigurationSnapshot, ContentConfigurationSnapshot | None]:
        with self._lock:
            current = self._versions.get(snapshot.id)
            if current is None:
                raise KeyError(snapshot.id)
            if current.state is not ContentConfigLifecycle.DRAFT:
                raise ValueError("only DRAFT content configuration may be published")

            previous = self.current_published()
            if previous is not None:
                self._versions[previous.id] = previous.with_state(ContentConfigLifecycle.SUPERSEDED)
            self._versions[snapshot.id] = deepcopy(snapshot)
            self._audit.append(deepcopy(audit))
            return deepcopy(snapshot), deepcopy(previous) if previous is not None else None

    def list_audit(self) -> tuple[ContentConfigurationAuditEntry, ...]:
        with self._lock:
            return tuple(deepcopy(item) for item in self._audit)
