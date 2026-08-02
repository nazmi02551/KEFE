from __future__ import annotations

from datetime import datetime, timedelta

from kefe_api.modules.content_supply_cycle.in_memory import (
    InMemoryContentSupplyCycleRepository,
)
from kefe_api.modules.content_supply_cycle.models import ContentSupplyCycleState
from kefe_api.modules.content_supply_health.models import (
    ContentSupplyOperationalFacts,
)
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.in_memory_leases import (
    InMemoryIngestionRunLeaseRepository,
)
from kefe_api.modules.ingestion_orchestration.leases import IngestionRunLeaseState
from kefe_api.modules.ingestion_orchestration.models import IngestionRunState
from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionDispatchState,
    SourceAcquisitionScheduleState,
)
from kefe_api.modules.knowledge.source_scheduler_memory import (
    InMemorySourceAcquisitionSchedulerRepository,
)

_DISPATCH_NON_SUCCESS_STATES = frozenset(
    {
        SourceAcquisitionDispatchState.RETRYABLE_FAILURE,
        SourceAcquisitionDispatchState.FINAL_FAILURE,
        SourceAcquisitionDispatchState.BLOCKED,
    }
)
_FAILED_RUN_STATES = frozenset(
    {IngestionRunState.FAILED_RETRYABLE, IngestionRunState.FAILED_FINAL}
)
_CYCLE_NON_SUCCESS_STATES = frozenset(
    {
        ContentSupplyCycleState.DEGRADED,
        ContentSupplyCycleState.FAILED,
        ContentSupplyCycleState.ABANDONED,
    }
)


class InMemoryContentSupplyOperationalFactsRepository:
    def __init__(
        self,
        *,
        scheduler: InMemorySourceAcquisitionSchedulerRepository,
        ingestion: InMemoryIngestionOrchestrationRepository,
        leases: InMemoryIngestionRunLeaseRepository,
        cycles: InMemoryContentSupplyCycleRepository,
    ) -> None:
        if leases._ingestion is not ingestion:
            raise ValueError("lease repository must share the ingestion repository")
        self._scheduler = scheduler
        self._ingestion = ingestion
        self._leases = leases
        self._cycles = cycles

    def read_facts(
        self,
        *,
        as_of: datetime,
        failure_window_seconds: int,
    ) -> ContentSupplyOperationalFacts:
        window_start = as_of - timedelta(seconds=failure_window_seconds)
        with self._scheduler._lock:
            with self._ingestion._lock:
                with self._cycles._lock:
                    schedules = tuple(self._scheduler._schedules.values())
                    dispatches = tuple(self._scheduler._dispatches.values())
                    runs = tuple(self._ingestion._runs.values())
                    leases = tuple(self._leases._leases.values())
                    proposals = tuple(self._ingestion._proposals.values())
                    decisions = tuple(self._ingestion._review_decisions.values())
                    cycles = tuple(self._cycles._cycles.values())

                    reviewed_proposal_ids = {
                        decision.proposal_id for decision in decisions
                    }
                    terminal_cycles = tuple(
                        cycle
                        for cycle in cycles
                        if cycle.state is not ContentSupplyCycleState.RUNNING
                    )
                    latest_terminal = max(
                        terminal_cycles,
                        key=lambda cycle: (cycle.completed_at, str(cycle.id)),
                        default=None,
                    )

                    return ContentSupplyOperationalFacts(
                        as_of=as_of,
                        active_schedule_count=sum(
                            schedule.state
                            is SourceAcquisitionScheduleState.ACTIVE
                            for schedule in schedules
                        ),
                        paused_schedule_count=sum(
                            schedule.state
                            is SourceAcquisitionScheduleState.PAUSED
                            for schedule in schedules
                        ),
                        due_schedule_count=sum(
                            schedule.state
                            is SourceAcquisitionScheduleState.ACTIVE
                            and schedule.next_due_at <= as_of
                            for schedule in schedules
                        ),
                        pending_dispatch_count=sum(
                            dispatch.state
                            is SourceAcquisitionDispatchState.PENDING
                            for dispatch in dispatches
                        ),
                        running_dispatch_count=sum(
                            dispatch.state
                            is SourceAcquisitionDispatchState.RUNNING
                            for dispatch in dispatches
                        ),
                        stale_dispatch_count=sum(
                            dispatch.state
                            is SourceAcquisitionDispatchState.RUNNING
                            and dispatch.expires_at is not None
                            and dispatch.expires_at <= as_of
                            for dispatch in dispatches
                        ),
                        recent_dispatch_non_success_count=sum(
                            dispatch.state in _DISPATCH_NON_SUCCESS_STATES
                            and dispatch.completed_at is not None
                            and dispatch.completed_at >= window_start
                            for dispatch in dispatches
                        ),
                        queued_ingestion_run_count=sum(
                            run.state is IngestionRunState.QUEUED for run in runs
                        ),
                        running_ingestion_run_count=sum(
                            run.state is IngestionRunState.RUNNING for run in runs
                        ),
                        stale_ingestion_lease_count=sum(
                            lease.state is IngestionRunLeaseState.ACTIVE
                            and lease.expires_at <= as_of
                            for lease in leases
                        ),
                        recent_failed_ingestion_run_count=sum(
                            run.state in _FAILED_RUN_STATES
                            and run.updated_at >= window_start
                            for run in runs
                        ),
                        unreviewed_proposal_count=sum(
                            proposal.id not in reviewed_proposal_ids
                            for proposal in proposals
                        ),
                        running_cycle_count=sum(
                            cycle.state is ContentSupplyCycleState.RUNNING
                            for cycle in cycles
                        ),
                        stale_cycle_count=sum(
                            cycle.state is ContentSupplyCycleState.RUNNING
                            and cycle.expires_at <= as_of
                            for cycle in cycles
                        ),
                        recent_non_success_cycle_count=sum(
                            cycle.state in _CYCLE_NON_SUCCESS_STATES
                            and cycle.completed_at is not None
                            and cycle.completed_at >= window_start
                            for cycle in cycles
                        ),
                        latest_terminal_cycle_state=(
                            latest_terminal.state.value
                            if latest_terminal is not None
                            else None
                        ),
                        latest_terminal_cycle_completed_at=(
                            latest_terminal.completed_at
                            if latest_terminal is not None
                            else None
                        ),
                    )
