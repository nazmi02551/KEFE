from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest
from sqlalchemy import create_engine

from kefe_api.infrastructure.postgres_content_supply_cycle import (
    PostgresContentSupplyCycleRepository,
)
from kefe_api.modules.content_supply_cycle.models import (
    ContentSupplyCycle,
    ContentSupplyCycleCommand,
    ContentSupplyCycleCounters,
    ContentSupplyCycleState,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _command(worker_ref: str = "postgres-cycle-worker") -> ContentSupplyCycleCommand:
    return ContentSupplyCycleCommand(
        worker_ref=worker_ref,
        plan_budget=2,
        dispatch_budget=2,
        pipeline_targets=(),
        cycle_ttl_seconds=30,
        dispatch_ttl_seconds=20,
        ingestion_ttl_seconds=20,
    )


def _cycle(
    *,
    command: ContentSupplyCycleCommand,
    started_at: datetime,
    ttl_seconds: int = 30,
) -> ContentSupplyCycle:
    return ContentSupplyCycle.start(
        command,
        started_at=started_at,
        expires_at=started_at + timedelta(seconds=ttl_seconds),
    )


def test_postgres_cycle_heartbeat_and_completion_require_exact_owner() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    repository = PostgresContentSupplyCycleRepository(engine)
    base = datetime.now(UTC).replace(microsecond=0)
    command = _command()
    created = repository.create(_cycle(command=command, started_at=base))
    counters = ContentSupplyCycleCounters(planned_count=1)

    with pytest.raises(ValueError, match="another worker"):
        repository.heartbeat(
            cycle_id=created.id,
            worker_ref="foreign-worker",
            heartbeat_at=base + timedelta(seconds=1),
            expires_at=base + timedelta(seconds=31),
            counters=counters,
        )

    heartbeat = repository.heartbeat(
        cycle_id=created.id,
        worker_ref=command.worker_ref,
        heartbeat_at=base + timedelta(seconds=1),
        expires_at=base + timedelta(seconds=31),
        counters=counters,
    )
    assert heartbeat.counters.planned_count == 1
    assert heartbeat.heartbeat_at == base + timedelta(seconds=1)

    completed = repository.complete(
        cycle_id=created.id,
        worker_ref=command.worker_ref,
        completed_at=base + timedelta(seconds=2),
        state=ContentSupplyCycleState.SUCCEEDED,
        counters=counters,
    )
    assert completed.state is ContentSupplyCycleState.SUCCEEDED
    assert completed.completed_at == base + timedelta(seconds=2)
    stored = repository.get(created.id)
    assert stored == completed


def test_postgres_stale_cycle_recovery_marks_abandoned_only() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    repository = PostgresContentSupplyCycleRepository(engine)
    base = datetime.now(UTC).replace(microsecond=0)
    command = _command("stale-cycle-worker")
    created = repository.create(
        _cycle(command=command, started_at=base, ttl_seconds=5)
    )

    assert repository.recover_stale(at=base + timedelta(seconds=4), limit=10) == ()
    recovered = repository.recover_stale(
        at=base + timedelta(seconds=6),
        limit=10,
    )

    assert len(recovered) == 1
    assert recovered[0].id == created.id
    assert recovered[0].state is ContentSupplyCycleState.ABANDONED
    assert recovered[0].error_code == "CONTENT_SUPPLY_CYCLE_STALE"
    assert repository.recover_stale(
        at=base + timedelta(seconds=7),
        limit=10,
    ) == ()


def test_postgres_concurrent_stale_recovery_abandons_cycle_once() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    base = datetime.now(UTC).replace(microsecond=0)
    command = _command("concurrent-recovery-worker")
    repository = PostgresContentSupplyCycleRepository(engine)
    created = repository.create(
        _cycle(command=command, started_at=base, ttl_seconds=5)
    )
    barrier = Barrier(2)

    def recover_once():
        local_repository = PostgresContentSupplyCycleRepository(engine)
        barrier.wait()
        return local_repository.recover_stale(
            at=base + timedelta(seconds=6),
            limit=1,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _: recover_once(), range(2)))

    recovered_ids = [cycle.id for batch in results for cycle in batch]
    assert recovered_ids == [created.id]
    stored = repository.get(created.id)
    assert stored is not None
    assert stored.state is ContentSupplyCycleState.ABANDONED


def test_postgres_terminal_cycle_is_not_changed_by_stale_recovery() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    repository = PostgresContentSupplyCycleRepository(engine)
    base = datetime.now(UTC).replace(microsecond=0)
    command = _command("terminal-cycle-worker")
    created = repository.create(_cycle(command=command, started_at=base))
    terminal = repository.complete(
        cycle_id=created.id,
        worker_ref=command.worker_ref,
        completed_at=base + timedelta(seconds=1),
        state=ContentSupplyCycleState.IDLE,
        counters=ContentSupplyCycleCounters(),
    )

    assert repository.recover_stale(
        at=base + timedelta(hours=1),
        limit=10,
    ) == ()
    assert repository.get(created.id) == terminal
