from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import RLock
from uuid import UUID

from kefe_api.modules.content_supply_cycle.models import (
    ContentSupplyCycle,
    ContentSupplyCycleCounters,
    ContentSupplyCycleState,
)


class InMemoryContentSupplyCycleRepository:
    def __init__(self) -> None:
        self._lock = RLock()
        self._cycles: dict[UUID, ContentSupplyCycle] = {}

    def create(self, cycle: ContentSupplyCycle) -> ContentSupplyCycle:
        with self._lock:
            if cycle.id in self._cycles:
                raise ValueError("content-supply cycle already exists")
            self._cycles[cycle.id] = deepcopy(cycle)
            return deepcopy(cycle)

    def get(self, cycle_id: UUID) -> ContentSupplyCycle | None:
        with self._lock:
            cycle = self._cycles.get(cycle_id)
            return deepcopy(cycle) if cycle is not None else None

    def heartbeat(
        self,
        *,
        cycle_id: UUID,
        worker_ref: str,
        heartbeat_at: datetime,
        expires_at: datetime,
        counters: ContentSupplyCycleCounters,
    ) -> ContentSupplyCycle:
        with self._lock:
            cycle = self._require(cycle_id)
            updated = cycle.heartbeat(
                worker_ref=worker_ref,
                at=heartbeat_at,
                expires_at=expires_at,
                counters=counters,
            )
            self._cycles[cycle_id] = updated
            return deepcopy(updated)

    def complete(
        self,
        *,
        cycle_id: UUID,
        worker_ref: str,
        completed_at: datetime,
        state: ContentSupplyCycleState,
        counters: ContentSupplyCycleCounters,
        error_code: str | None = None,
    ) -> ContentSupplyCycle:
        with self._lock:
            cycle = self._require(cycle_id)
            updated = cycle.complete(
                worker_ref=worker_ref,
                at=completed_at,
                state=state,
                counters=counters,
                error_code=error_code,
            )
            self._cycles[cycle_id] = updated
            return deepcopy(updated)

    def recover_stale(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[ContentSupplyCycle, ...]:
        if limit < 1:
            raise ValueError("stale recovery limit must be positive")
        with self._lock:
            stale = sorted(
                (
                    cycle
                    for cycle in self._cycles.values()
                    if cycle.state is ContentSupplyCycleState.RUNNING
                    and cycle.expires_at <= at
                ),
                key=lambda cycle: (cycle.expires_at, str(cycle.id)),
            )[:limit]
            recovered: list[ContentSupplyCycle] = []
            for cycle in stale:
                updated = cycle.abandon(at=at)
                self._cycles[cycle.id] = updated
                recovered.append(deepcopy(updated))
            return tuple(recovered)

    def _require(self, cycle_id: UUID) -> ContentSupplyCycle:
        try:
            return self._cycles[cycle_id]
        except KeyError as exc:
            raise KeyError(cycle_id) from exc
