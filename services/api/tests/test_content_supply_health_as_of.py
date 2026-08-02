from __future__ import annotations

from datetime import UTC, datetime, timedelta

from kefe_api.modules.content_supply_cycle.in_memory import (
    InMemoryContentSupplyCycleRepository,
)
from kefe_api.modules.content_supply_cycle.models import (
    ContentSupplyCycle,
    ContentSupplyCycleCommand,
    ContentSupplyCycleCounters,
    ContentSupplyCycleState,
)
from kefe_api.modules.content_supply_health.in_memory import (
    InMemoryContentSupplyOperationalFactsRepository,
)
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.in_memory_leases import (
    InMemoryIngestionRunLeaseRepository,
)
from kefe_api.modules.knowledge.source_scheduler_memory import (
    InMemorySourceAcquisitionSchedulerRepository,
)


def _terminal_cycle(
    *,
    worker_ref: str,
    completed_at: datetime,
    state: ContentSupplyCycleState,
) -> ContentSupplyCycle:
    command = ContentSupplyCycleCommand(
        worker_ref=worker_ref,
        plan_budget=0,
        dispatch_budget=0,
        pipeline_targets=(),
        cycle_ttl_seconds=600,
        dispatch_ttl_seconds=60,
        ingestion_ttl_seconds=60,
    )
    running = ContentSupplyCycle.start(
        command,
        started_at=completed_at - timedelta(minutes=1),
        expires_at=completed_at + timedelta(minutes=9),
    )
    error_code = (
        None
        if state in {ContentSupplyCycleState.IDLE, ContentSupplyCycleState.SUCCEEDED}
        else "BOUNDED_NON_SUCCESS"
    )
    return running.complete(
        worker_ref=worker_ref,
        at=completed_at,
        state=state,
        counters=ContentSupplyCycleCounters(),
        error_code=error_code,
    )


def test_memory_snapshot_excludes_future_terminal_cycles_from_latest_and_recent() -> None:
    as_of = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    scheduler = InMemorySourceAcquisitionSchedulerRepository()
    ingestion = InMemoryIngestionOrchestrationRepository()
    leases = InMemoryIngestionRunLeaseRepository(ingestion)
    cycles = InMemoryContentSupplyCycleRepository()
    past = _terminal_cycle(
        worker_ref="past-cycle",
        completed_at=as_of - timedelta(seconds=30),
        state=ContentSupplyCycleState.SUCCEEDED,
    )
    future = _terminal_cycle(
        worker_ref="future-cycle",
        completed_at=as_of + timedelta(seconds=30),
        state=ContentSupplyCycleState.FAILED,
    )
    cycles.create(past)
    cycles.create(future)

    facts = InMemoryContentSupplyOperationalFactsRepository(
        scheduler=scheduler,
        ingestion=ingestion,
        leases=leases,
        cycles=cycles,
    ).read_facts(as_of=as_of, failure_window_seconds=3600)

    assert facts.latest_terminal_cycle_state == "SUCCEEDED"
    assert facts.latest_terminal_cycle_completed_at == past.completed_at
    assert facts.recent_non_success_cycle_count == 0
