from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.content_supply_cycle.models import (
    ContentSupplyCycle,
    ContentSupplyCycleCounters,
    ContentSupplyCycleState,
)


class ContentSupplyCycleRepository(Protocol):
    def create(self, cycle: ContentSupplyCycle) -> ContentSupplyCycle: ...

    def get(self, cycle_id: UUID) -> ContentSupplyCycle | None: ...

    def heartbeat(
        self,
        *,
        cycle_id: UUID,
        worker_ref: str,
        heartbeat_at: datetime,
        expires_at: datetime,
        counters: ContentSupplyCycleCounters,
    ) -> ContentSupplyCycle: ...

    def complete(
        self,
        *,
        cycle_id: UUID,
        worker_ref: str,
        completed_at: datetime,
        state: ContentSupplyCycleState,
        counters: ContentSupplyCycleCounters,
        error_code: str | None = None,
    ) -> ContentSupplyCycle: ...

    def recover_stale(
        self,
        *,
        at: datetime,
        limit: int,
    ) -> tuple[ContentSupplyCycle, ...]: ...
