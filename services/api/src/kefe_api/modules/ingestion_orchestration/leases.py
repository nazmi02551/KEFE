from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.models import IngestionRun, require_text


class IngestionRunLeaseState(StrEnum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


class IngestionRunLeaseReleaseDisposition(StrEnum):
    REQUEUE = "REQUEUE"
    TERMINAL = "TERMINAL"


@dataclass(frozen=True, slots=True)
class IngestionRunLease:
    id: UUID
    run_id: UUID
    worker_ref: str
    state: IngestionRunLeaseState
    claimed_at: datetime
    heartbeat_at: datetime
    expires_at: datetime
    released_at: datetime | None = None
    release_disposition: IngestionRunLeaseReleaseDisposition | None = None

    def __post_init__(self) -> None:
        require_text(self.worker_ref, "worker_ref")
        for value, field_name in (
            (self.claimed_at, "claimed_at"),
            (self.heartbeat_at, "heartbeat_at"),
            (self.expires_at, "expires_at"),
        ):
            if value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware")
        if self.heartbeat_at < self.claimed_at:
            raise ValueError("heartbeat_at must not precede claimed_at")
        if self.expires_at <= self.heartbeat_at:
            raise ValueError("expires_at must be after heartbeat_at")
        if self.released_at is not None and self.released_at.tzinfo is None:
            raise ValueError("released_at must be timezone-aware")
        if self.state is IngestionRunLeaseState.ACTIVE:
            if self.released_at is not None or self.release_disposition is not None:
                raise ValueError("active lease cannot have release metadata")
        elif self.state is IngestionRunLeaseState.EXPIRED:
            if self.released_at is None or self.release_disposition is not None:
                raise ValueError("expired lease requires released_at only")
        elif self.released_at is None or self.release_disposition is None:
            raise ValueError("released lease requires disposition and released_at")

    def is_active_at(self, at: datetime) -> bool:
        return self.state is IngestionRunLeaseState.ACTIVE and self.expires_at > at

    def heartbeat(self, *, at: datetime, expires_at: datetime) -> IngestionRunLease:
        if not self.is_active_at(at):
            raise ValueError("ingestion run lease is not active")
        return replace(self, heartbeat_at=at, expires_at=expires_at)

    def release(
        self,
        *,
        at: datetime,
        disposition: IngestionRunLeaseReleaseDisposition,
    ) -> IngestionRunLease:
        if not self.is_active_at(at):
            raise ValueError("ingestion run lease is not active")
        return replace(
            self,
            state=IngestionRunLeaseState.RELEASED,
            released_at=at,
            release_disposition=disposition,
        )

    def expire(self, *, at: datetime) -> IngestionRunLease:
        if self.state is not IngestionRunLeaseState.ACTIVE:
            raise ValueError("only an active ingestion run lease can expire")
        if self.expires_at > at:
            raise ValueError("ingestion run lease has not expired")
        return replace(
            self,
            state=IngestionRunLeaseState.EXPIRED,
            released_at=at,
        )


@dataclass(frozen=True, slots=True)
class IngestionRunLeaseClaim:
    run: IngestionRun
    lease: IngestionRunLease
