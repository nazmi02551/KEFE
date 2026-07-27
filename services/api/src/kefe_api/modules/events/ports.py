from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.events.models import OutboxEvent


class OutboxStore(Protocol):
    def claim_batch(
        self,
        *,
        worker_id: str,
        limit: int,
        lease_seconds: int,
    ) -> list[OutboxEvent]: ...

    def mark_published(self, *, event_id: UUID, worker_id: str) -> None: ...

    def mark_failed(
        self,
        *,
        event_id: UUID,
        worker_id: str,
        error: str,
        next_attempt_at: datetime,
        dead_letter: bool,
    ) -> None: ...


class EventTransport(Protocol):
    def publish(self, event: OutboxEvent) -> None: ...
