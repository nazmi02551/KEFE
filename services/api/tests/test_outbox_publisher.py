from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from kefe_api.modules.events.models import OutboxEvent
from kefe_api.modules.events.service import OutboxPublisher, RetryPolicy


class FakeStore:
    def __init__(self, events: list[OutboxEvent]) -> None:
        self.events = events
        self.published: list[str] = []
        self.failed: list[dict[str, object]] = []

    def claim_batch(self, *, worker_id: str, limit: int, lease_seconds: int):
        del worker_id, lease_seconds
        return self.events[:limit]

    def mark_published(self, *, event_id, worker_id: str) -> None:
        del worker_id
        self.published.append(str(event_id))

    def mark_failed(
        self,
        *,
        event_id,
        worker_id: str,
        error: str,
        next_attempt_at,
        dead_letter: bool,
    ) -> None:
        del worker_id
        self.failed.append(
            {
                "event_id": str(event_id),
                "error": error,
                "next_attempt_at": next_attempt_at,
                "dead_letter": dead_letter,
            }
        )


class RecordingTransport:
    def __init__(self, fail_names: set[str] | None = None) -> None:
        self.fail_names = fail_names or set()
        self.published: list[str] = []

    def publish(self, event: OutboxEvent) -> None:
        if event.event_name in self.fail_names:
            raise RuntimeError("provider unavailable")
        self.published.append(event.event_name)


def _event(name: str, *, attempts: int = 1) -> OutboxEvent:
    return OutboxEvent(
        id=uuid4(),
        aggregate_type="WEIGH_SESSION",
        aggregate_id=uuid4(),
        event_name=name,
        event_version=1,
        occurred_at=datetime.now(UTC),
        payload={"example": True},
        attempts=attempts,
    )


def test_outbox_publishes_successful_events() -> None:
    events = [_event("weigh.started"), _event("weigh.committed")]
    store = FakeStore(events)
    transport = RecordingTransport()
    publisher = OutboxPublisher(
        store=store,
        transport=transport,
        retry_policy=RetryPolicy(),
        worker_id="test-worker",
    )

    result = publisher.run_once()

    assert result.claimed == 2
    assert result.published == 2
    assert result.failed == 0
    assert transport.published == ["weigh.started", "weigh.committed"]
    assert len(store.published) == 2


def test_outbox_failure_is_scheduled_for_retry() -> None:
    event = _event("weigh.committed", attempts=2)
    store = FakeStore([event])
    transport = RecordingTransport({"weigh.committed"})
    publisher = OutboxPublisher(
        store=store,
        transport=transport,
        retry_policy=RetryPolicy(base_seconds=5, max_seconds=100, max_attempts=8),
        worker_id="test-worker",
    )

    before = datetime.now(UTC)
    result = publisher.run_once()

    assert result.failed == 1
    assert result.dead_lettered == 0
    assert store.failed[0]["dead_letter"] is False
    assert store.failed[0]["next_attempt_at"] >= before


def test_outbox_failure_dead_letters_at_attempt_limit() -> None:
    event = _event("weigh.committed", attempts=8)
    store = FakeStore([event])
    publisher = OutboxPublisher(
        store=store,
        transport=RecordingTransport({"weigh.committed"}),
        retry_policy=RetryPolicy(max_attempts=8),
        worker_id="test-worker",
    )

    result = publisher.run_once()

    assert result.failed == 1
    assert result.dead_lettered == 1
    assert store.failed[0]["dead_letter"] is True


def test_retry_backoff_is_bounded() -> None:
    policy = RetryPolicy(base_seconds=5, max_seconds=60, max_attempts=8)

    assert policy.delay_for_attempt(1).total_seconds() == 5
    assert policy.delay_for_attempt(2).total_seconds() == 10
    assert policy.delay_for_attempt(20).total_seconds() == 60
