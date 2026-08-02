from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from uuid import UUID, uuid4

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.leases import (
    IngestionRunLease,
    IngestionRunLeaseClaim,
    IngestionRunLeaseReleaseDisposition,
    IngestionRunLeaseState,
)
from kefe_api.modules.ingestion_orchestration.models import IngestionRunState

_TERMINAL_RELEASE_STATES = frozenset(
    {
        IngestionRunState.SUCCEEDED,
        IngestionRunState.FAILED_RETRYABLE,
        IngestionRunState.FAILED_FINAL,
        IngestionRunState.CANCELED,
    }
)


class InMemoryIngestionRunLeaseRepository:
    """Lease history sharing the ingestion repository's critical section and run store."""

    def __init__(
        self,
        ingestion_repository: InMemoryIngestionOrchestrationRepository,
    ) -> None:
        self._ingestion = ingestion_repository
        self._leases: dict[UUID, IngestionRunLease] = {}
        self._active_by_run: dict[UUID, UUID] = {}

    def claim_next(
        self,
        *,
        worker_ref: str,
        claimed_at: datetime,
        expires_at: datetime,
        pipeline_code: str | None = None,
    ) -> IngestionRunLeaseClaim | None:
        with self._ingestion._lock:
            self._recover_expired_locked(at=claimed_at, limit=1000)
            candidates = [
                run
                for run in self._ingestion._runs.values()
                if run.state is IngestionRunState.QUEUED
                and run.id not in self._active_by_run
                and (pipeline_code is None or run.pipeline_code == pipeline_code)
            ]
            if not candidates:
                return None
            selected = min(candidates, key=lambda run: (run.updated_at, str(run.id)))
            running = selected.transition(IngestionRunState.RUNNING, at=claimed_at)
            lease = IngestionRunLease(
                id=uuid4(),
                run_id=selected.id,
                worker_ref=worker_ref,
                state=IngestionRunLeaseState.ACTIVE,
                claimed_at=claimed_at,
                heartbeat_at=claimed_at,
                expires_at=expires_at,
            )
            self._ingestion._runs[selected.id] = deepcopy(running)
            self._leases[lease.id] = deepcopy(lease)
            self._active_by_run[selected.id] = lease.id
            return IngestionRunLeaseClaim(
                run=deepcopy(running),
                lease=deepcopy(lease),
            )

    def heartbeat(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        heartbeat_at: datetime,
        expires_at: datetime,
    ) -> IngestionRunLease:
        with self._ingestion._lock:
            lease = self._require_owned_active(lease_id, worker_ref, heartbeat_at)
            updated = lease.heartbeat(at=heartbeat_at, expires_at=expires_at)
            self._leases[lease_id] = deepcopy(updated)
            return deepcopy(updated)

    def assert_active(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        at: datetime,
    ) -> IngestionRunLease:
        with self._ingestion._lock:
            return deepcopy(self._require_owned_active(lease_id, worker_ref, at))

    def release(
        self,
        *,
        lease_id: UUID,
        worker_ref: str,
        released_at: datetime,
        disposition: IngestionRunLeaseReleaseDisposition,
    ) -> IngestionRunLease:
        with self._ingestion._lock:
            lease = self._require_owned_active(lease_id, worker_ref, released_at)
            run = self._ingestion._runs.get(lease.run_id)
            if run is None:
                raise KeyError(lease.run_id)
            if disposition is IngestionRunLeaseReleaseDisposition.REQUEUE:
                if run.state is not IngestionRunState.RUNNING:
                    raise ValueError("REQUEUE release requires RUNNING run")
                self._ingestion._runs[run.id] = deepcopy(
                    run.transition(IngestionRunState.QUEUED, at=released_at)
                )
            elif run.state not in _TERMINAL_RELEASE_STATES:
                raise ValueError("TERMINAL release requires terminal run")

            released = lease.release(at=released_at, disposition=disposition)
            self._leases[lease_id] = deepcopy(released)
            self._active_by_run.pop(lease.run_id, None)
            return deepcopy(released)

    def recover_expired(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[IngestionRunLease, ...]:
        with self._ingestion._lock:
            return tuple(
                deepcopy(item)
                for item in self._recover_expired_locked(at=at, limit=limit)
            )

    def get_lease(self, lease_id: UUID) -> IngestionRunLease | None:
        with self._ingestion._lock:
            lease = self._leases.get(lease_id)
            return deepcopy(lease) if lease else None

    def _recover_expired_locked(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[IngestionRunLease, ...]:
        due = sorted(
            (
                lease
                for lease in self._leases.values()
                if lease.state is IngestionRunLeaseState.ACTIVE
                and lease.expires_at <= at
            ),
            key=lambda lease: (lease.expires_at, str(lease.id)),
        )[:limit]
        recovered: list[IngestionRunLease] = []
        for lease in due:
            expired = lease.expire(at=at)
            self._leases[lease.id] = deepcopy(expired)
            self._active_by_run.pop(lease.run_id, None)
            run = self._ingestion._runs.get(lease.run_id)
            if run is not None and run.state is IngestionRunState.RUNNING:
                self._ingestion._runs[run.id] = deepcopy(
                    run.transition(IngestionRunState.QUEUED, at=at)
                )
            recovered.append(expired)
        return tuple(recovered)

    def _require_owned_active(
        self,
        lease_id: UUID,
        worker_ref: str,
        at: datetime,
    ) -> IngestionRunLease:
        lease = self._leases.get(lease_id)
        if lease is None:
            raise KeyError(lease_id)
        if lease.worker_ref != worker_ref:
            raise ValueError("ingestion run lease belongs to another worker")
        if self._active_by_run.get(lease.run_id) != lease.id:
            raise ValueError("ingestion run lease is not the active run lease")
        if not lease.is_active_at(at):
            raise ValueError("ingestion run lease is not active")
        return lease
