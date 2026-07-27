from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.events.models import PublishResult
from kefe_api.modules.events.ports import EventTransport, OutboxStore


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    base_seconds: int = 5
    max_seconds: int = 900
    max_attempts: int = 8

    def delay_for_attempt(self, attempt: int) -> timedelta:
        exponent = max(0, attempt - 1)
        seconds = min(self.max_seconds, self.base_seconds * (2**exponent))
        return timedelta(seconds=seconds)


class OutboxPublisher:
    def __init__(
        self,
        *,
        store: OutboxStore,
        transport: EventTransport,
        retry_policy: RetryPolicy,
        batch_size: int = 100,
        lease_seconds: int = 30,
        worker_id: str | None = None,
    ) -> None:
        self._store = store
        self._transport = transport
        self._retry_policy = retry_policy
        self._batch_size = batch_size
        self._lease_seconds = lease_seconds
        self._worker_id = worker_id or f"outbox-{uuid4()}"

    def run_once(self) -> PublishResult:
        events = self._store.claim_batch(
            worker_id=self._worker_id,
            limit=self._batch_size,
            lease_seconds=self._lease_seconds,
        )
        published = 0
        failed = 0
        dead_lettered = 0

        for event in events:
            try:
                self._transport.publish(event)
            except Exception as exc:  # transport/provider boundary
                failed += 1
                dead_letter = event.attempts >= self._retry_policy.max_attempts
                if dead_letter:
                    dead_lettered += 1
                next_attempt_at = datetime.now(UTC) + self._retry_policy.delay_for_attempt(
                    event.attempts
                )
                self._store.mark_failed(
                    event_id=event.id,
                    worker_id=self._worker_id,
                    error=str(exc)[:2000],
                    next_attempt_at=next_attempt_at,
                    dead_letter=dead_letter,
                )
            else:
                self._store.mark_published(event_id=event.id, worker_id=self._worker_id)
                published += 1

        return PublishResult(
            claimed=len(events),
            published=published,
            failed=failed,
            dead_lettered=dead_lettered,
        )
