from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock
from typing import Protocol
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition


class PublicFeedCatalogState(StrEnum):
    REGISTERED = "REGISTERED"
    MANUAL_CAPTURE_APPROVED = "MANUAL_CAPTURE_APPROVED"
    RETIRED = "RETIRED"


_ALLOWED_TRANSITIONS = {
    PublicFeedCatalogState.REGISTERED: frozenset(
        {
            PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED,
            PublicFeedCatalogState.RETIRED,
        }
    ),
    PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED: frozenset(
        {PublicFeedCatalogState.RETIRED}
    ),
    PublicFeedCatalogState.RETIRED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class PublicFeedCatalogEntry:
    id: UUID
    definition: PublicFeedDefinition
    configuration_hash: str
    state: PublicFeedCatalogState
    registered_by: str
    registered_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None
    retired_by: str | None = None
    retired_at: datetime | None = None
    retirement_rationale: str | None = None

    def __post_init__(self) -> None:
        if type(self.definition) is not PublicFeedDefinition:
            raise ValueError("definition must be exact PublicFeedDefinition")
        if self.configuration_hash != self.definition.configuration_hash:
            raise ValueError("configuration_hash must match immutable definition")
        if not self.registered_by.strip():
            raise ValueError("registered_by must not be blank")
        _require_utc(self.registered_at, "registered_at")
        if type(self.state) is not PublicFeedCatalogState:
            raise ValueError("state must be exact PublicFeedCatalogState")
        if self.state is PublicFeedCatalogState.REGISTERED:
            if any(
                value is not None
                for value in (
                    self.approved_by,
                    self.approved_at,
                    self.retired_by,
                    self.retired_at,
                    self.retirement_rationale,
                )
            ):
                raise ValueError("REGISTERED entry cannot contain transition metadata")
        elif self.state is PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED:
            if not self.approved_by or self.approved_at is None:
                raise ValueError("approved entry requires approval metadata")
            _require_utc(self.approved_at, "approved_at")
            if any(
                value is not None
                for value in (
                    self.retired_by,
                    self.retired_at,
                    self.retirement_rationale,
                )
            ):
                raise ValueError("approved entry cannot contain retirement metadata")
        else:
            if not self.retired_by or self.retired_at is None:
                raise ValueError("retired entry requires retirement metadata")
            _require_utc(self.retired_at, "retired_at")
            if not self.retirement_rationale or not self.retirement_rationale.strip():
                raise ValueError("retirement_rationale must not be blank")
            if len(self.retirement_rationale) > 5000:
                raise ValueError("retirement_rationale is too long")
            if self.approved_at is not None:
                _require_utc(self.approved_at, "approved_at")

    @property
    def feed_code(self) -> str:
        return self.definition.feed_code

    @property
    def adapter_code(self) -> str:
        return self.definition.adapter_code

    @property
    def immutable_identity(self) -> tuple[object, ...]:
        return (
            self.definition,
            self.configuration_hash,
            self.registered_by,
            self.registered_at,
        )

    def transition(
        self,
        target: PublicFeedCatalogState,
        *,
        actor_ref: str,
        at: datetime,
        rationale: str | None = None,
    ) -> PublicFeedCatalogEntry:
        if target not in _ALLOWED_TRANSITIONS[self.state]:
            raise ValueError("public feed catalog transition is invalid")
        if not actor_ref.strip():
            raise ValueError("actor_ref must not be blank")
        _require_utc(at, "at")
        if target is PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED:
            return replace(
                self,
                state=target,
                approved_by=actor_ref,
                approved_at=at,
            )
        if rationale is None or not rationale.strip() or len(rationale) > 5000:
            raise ValueError("retirement rationale is invalid")
        return replace(
            self,
            state=target,
            retired_by=actor_ref,
            retired_at=at,
            retirement_rationale=rationale,
        )


@dataclass(frozen=True, slots=True)
class PublicFeedCatalogAuditEntry:
    audit_id: UUID
    catalog_entry_id: UUID
    feed_code: str
    actor_ref: str
    command: str
    previous_state: PublicFeedCatalogState | None
    new_state: PublicFeedCatalogState
    occurred_at: datetime
    rationale: str | None = None

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.feed_code, "feed_code"),
            (self.actor_ref, "actor_ref"),
            (self.command, "command"),
        ):
            if not value.strip():
                raise ValueError(f"{field_name} must not be blank")
        _require_utc(self.occurred_at, "occurred_at")


class PublicFeedCatalogConflictError(Exception):
    pass


class PublicFeedCatalogRepository(Protocol):
    def register(
        self,
        entry: PublicFeedCatalogEntry,
        audit: PublicFeedCatalogAuditEntry,
    ) -> PublicFeedCatalogEntry: ...

    def get(self, entry_id: UUID) -> PublicFeedCatalogEntry | None: ...

    def get_by_feed_code(self, feed_code: str) -> PublicFeedCatalogEntry | None: ...

    def list_entries(self) -> tuple[PublicFeedCatalogEntry, ...]: ...

    def transition(
        self,
        entry: PublicFeedCatalogEntry,
        audit: PublicFeedCatalogAuditEntry,
    ) -> PublicFeedCatalogEntry: ...

    def list_audit(
        self,
        entry_id: UUID | None = None,
    ) -> tuple[PublicFeedCatalogAuditEntry, ...]: ...


class InMemoryPublicFeedCatalogRepository:
    def __init__(self) -> None:
        self._entries: dict[UUID, PublicFeedCatalogEntry] = {}
        self._by_feed_code: dict[str, UUID] = {}
        self._by_adapter_code: dict[str, UUID] = {}
        self._audit: list[PublicFeedCatalogAuditEntry] = []
        self._lock = Lock()

    def register(
        self,
        entry: PublicFeedCatalogEntry,
        audit: PublicFeedCatalogAuditEntry,
    ) -> PublicFeedCatalogEntry:
        with self._lock:
            feed_id = self._by_feed_code.get(entry.feed_code)
            adapter_id = self._by_adapter_code.get(entry.adapter_code)
            if feed_id is not None:
                existing = self._entries[feed_id]
                if (
                    existing.definition == entry.definition
                    and existing.configuration_hash == entry.configuration_hash
                ):
                    return existing
                raise PublicFeedCatalogConflictError(entry.feed_code)
            if adapter_id is not None:
                raise PublicFeedCatalogConflictError(entry.adapter_code)
            self._entries[entry.id] = entry
            self._by_feed_code[entry.feed_code] = entry.id
            self._by_adapter_code[entry.adapter_code] = entry.id
            self._audit.append(audit)
            return entry

    def get(self, entry_id: UUID) -> PublicFeedCatalogEntry | None:
        with self._lock:
            return self._entries.get(entry_id)

    def get_by_feed_code(self, feed_code: str) -> PublicFeedCatalogEntry | None:
        with self._lock:
            entry_id = self._by_feed_code.get(feed_code)
            return self._entries.get(entry_id) if entry_id is not None else None

    def list_entries(self) -> tuple[PublicFeedCatalogEntry, ...]:
        with self._lock:
            return tuple(
                sorted(
                    self._entries.values(),
                    key=lambda item: (item.feed_code, str(item.id)),
                )
            )

    def transition(
        self,
        entry: PublicFeedCatalogEntry,
        audit: PublicFeedCatalogAuditEntry,
    ) -> PublicFeedCatalogEntry:
        with self._lock:
            current = self._entries.get(entry.id)
            if current is None:
                raise KeyError(entry.id)
            if current.definition != entry.definition:
                raise PublicFeedCatalogConflictError(entry.feed_code)
            if current.state is not audit.previous_state:
                raise PublicFeedCatalogConflictError(entry.feed_code)
            self._entries[entry.id] = entry
            self._audit.append(audit)
            return entry

    def list_audit(
        self,
        entry_id: UUID | None = None,
    ) -> tuple[PublicFeedCatalogAuditEntry, ...]:
        with self._lock:
            return tuple(
                item
                for item in self._audit
                if entry_id is None or item.catalog_entry_id == entry_id
            )


class PublicFeedCatalogService:
    def __init__(
        self,
        *,
        repository: PublicFeedCatalogRepository,
        security: AdminSecurityService,
        clock=lambda: datetime.now(UTC),
    ) -> None:
        self._repository = repository
        self._security = security
        self._clock = clock

    def list_entries(
        self,
        principal: AdminPrincipal,
    ) -> tuple[PublicFeedCatalogEntry, ...]:
        self._security.authorize(principal, AdminCapability.SOURCE_MANAGE)
        return self._repository.list_entries()

    def get(
        self,
        principal: AdminPrincipal,
        entry_id: UUID,
    ) -> PublicFeedCatalogEntry:
        self._security.authorize(principal, AdminCapability.SOURCE_MANAGE)
        entry = self._repository.get(entry_id)
        if entry is None:
            raise DomainError(
                "PUBLIC_FEED_CATALOG_NOT_FOUND",
                "Public feed catalog entry was not found",
                404,
            )
        return entry

    def register(
        self,
        principal: AdminPrincipal,
        definition: PublicFeedDefinition,
    ) -> PublicFeedCatalogEntry:
        self._security.authorize(principal, AdminCapability.SOURCE_MANAGE)
        now = self._clock()
        entry = PublicFeedCatalogEntry(
            id=uuid4(),
            definition=definition,
            configuration_hash=definition.configuration_hash,
            state=PublicFeedCatalogState.REGISTERED,
            registered_by=principal.audit_actor_ref,
            registered_at=now,
        )
        audit = PublicFeedCatalogAuditEntry(
            audit_id=uuid4(),
            catalog_entry_id=entry.id,
            feed_code=entry.feed_code,
            actor_ref=principal.audit_actor_ref,
            command="REGISTER",
            previous_state=None,
            new_state=entry.state,
            occurred_at=now,
        )
        try:
            return self._repository.register(entry, audit)
        except PublicFeedCatalogConflictError as exc:
            raise DomainError(
                "PUBLIC_FEED_CATALOG_CONFLICT",
                "Public feed code or adapter code conflicts with an existing entry",
                409,
            ) from exc

    def approve_manual_capture(
        self,
        principal: AdminPrincipal,
        entry_id: UUID,
    ) -> PublicFeedCatalogEntry:
        self._security.authorize(principal, AdminCapability.SOURCE_MANAGE)
        self._security.require_fresh_step_up(principal)
        return self._transition(
            principal=principal,
            entry_id=entry_id,
            target=PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED,
            command="APPROVE_MANUAL_CAPTURE",
        )

    def retire(
        self,
        principal: AdminPrincipal,
        entry_id: UUID,
        *,
        rationale: str,
    ) -> PublicFeedCatalogEntry:
        self._security.authorize(principal, AdminCapability.SOURCE_MANAGE)
        self._security.require_fresh_step_up(principal)
        return self._transition(
            principal=principal,
            entry_id=entry_id,
            target=PublicFeedCatalogState.RETIRED,
            command="RETIRE",
            rationale=rationale,
        )

    def list_audit(
        self,
        principal: AdminPrincipal,
        entry_id: UUID | None = None,
    ) -> tuple[PublicFeedCatalogAuditEntry, ...]:
        self._security.authorize(principal, AdminCapability.SOURCE_MANAGE)
        return self._repository.list_audit(entry_id)

    def _transition(
        self,
        *,
        principal: AdminPrincipal,
        entry_id: UUID,
        target: PublicFeedCatalogState,
        command: str,
        rationale: str | None = None,
    ) -> PublicFeedCatalogEntry:
        current = self._repository.get(entry_id)
        if current is None:
            raise DomainError(
                "PUBLIC_FEED_CATALOG_NOT_FOUND",
                "Public feed catalog entry was not found",
                404,
            )
        now = self._clock()
        try:
            updated = current.transition(
                target,
                actor_ref=principal.audit_actor_ref,
                at=now,
                rationale=rationale,
            )
        except ValueError as exc:
            raise DomainError(
                "PUBLIC_FEED_CATALOG_TRANSITION_INVALID",
                "Public feed catalog lifecycle transition is invalid",
                409,
            ) from exc
        audit = PublicFeedCatalogAuditEntry(
            audit_id=uuid4(),
            catalog_entry_id=current.id,
            feed_code=current.feed_code,
            actor_ref=principal.audit_actor_ref,
            command=command,
            previous_state=current.state,
            new_state=updated.state,
            occurred_at=now,
            rationale=rationale,
        )
        try:
            return self._repository.transition(updated, audit)
        except PublicFeedCatalogConflictError as exc:
            raise DomainError(
                "PUBLIC_FEED_CATALOG_CONFLICT",
                "Public feed catalog entry changed concurrently",
                409,
            ) from exc


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


__all__ = [
    "InMemoryPublicFeedCatalogRepository",
    "PublicFeedCatalogAuditEntry",
    "PublicFeedCatalogConflictError",
    "PublicFeedCatalogEntry",
    "PublicFeedCatalogRepository",
    "PublicFeedCatalogService",
    "PublicFeedCatalogState",
]
