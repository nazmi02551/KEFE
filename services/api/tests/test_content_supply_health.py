from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.content_supply_cycle.in_memory import (
    InMemoryContentSupplyCycleRepository,
)
from kefe_api.modules.content_supply_cycle.models import (
    ContentSupplyCycle,
    ContentSupplyCycleCounters,
    ContentSupplyCycleState,
)
from kefe_api.modules.content_supply_health.in_memory import (
    InMemoryContentSupplyOperationalFactsRepository,
)
from kefe_api.modules.content_supply_health.models import (
    ContentSupplyHealthPolicy,
    ContentSupplyHealthSignal,
    ContentSupplyOperationalFacts,
)
from kefe_api.modules.content_supply_health.service import ContentSupplyHealthService
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.in_memory_leases import (
    InMemoryIngestionRunLeaseRepository,
)
from kefe_api.modules.ingestion_orchestration.leases import (
    IngestionRunLease,
    IngestionRunLeaseState,
)
from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    stable_payload_hash,
)
from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionDispatch,
    SourceAcquisitionDispatchState,
    SourceAcquisitionSchedule,
    SourceAcquisitionScheduleState,
)
from kefe_api.modules.knowledge.source_scheduler_memory import (
    InMemorySourceAcquisitionSchedulerRepository,
)


class StaticFactsRepository:
    def __init__(self, facts: ContentSupplyOperationalFacts) -> None:
        self.facts = facts
        self.calls = []

    def read_facts(self, *, as_of, failure_window_seconds):
        self.calls.append((as_of, failure_window_seconds))
        return self.facts


def _facts(as_of: datetime, **changes) -> ContentSupplyOperationalFacts:
    values = {"as_of": as_of}
    values.update(changes)
    return ContentSupplyOperationalFacts(**values)


def test_quiet_and_nominal_signals_are_distinct() -> None:
    base = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    quiet = ContentSupplyHealthService(StaticFactsRepository(_facts(base))).snapshot(
        ContentSupplyHealthPolicy(),
        as_of=base,
    )
    nominal = ContentSupplyHealthService(
        StaticFactsRepository(
            _facts(
                base,
                active_schedule_count=1,
                latest_terminal_cycle_state="SUCCEEDED",
                latest_terminal_cycle_completed_at=base - timedelta(minutes=5),
            )
        )
    ).snapshot(ContentSupplyHealthPolicy(), as_of=base)

    assert quiet.signal is ContentSupplyHealthSignal.QUIET
    assert quiet.reason_codes == ()
    assert nominal.signal is ContentSupplyHealthSignal.NOMINAL
    assert nominal.reason_codes == ()
    assert nominal.seconds_since_latest_terminal_cycle == 300


def test_attention_reasons_are_explicit_sorted_and_threshold_driven() -> None:
    base = datetime(2026, 8, 2, 13, 0, tzinfo=UTC)
    facts = _facts(
        base,
        active_schedule_count=1,
        pending_dispatch_count=2,
        recent_dispatch_non_success_count=1,
        queued_ingestion_run_count=2,
        recent_failed_ingestion_run_count=1,
        unreviewed_proposal_count=2,
        recent_non_success_cycle_count=1,
        latest_terminal_cycle_state="DEGRADED",
        latest_terminal_cycle_completed_at=base - timedelta(hours=2),
    )
    snapshot = ContentSupplyHealthService(StaticFactsRepository(facts)).snapshot(
        ContentSupplyHealthPolicy(
            pending_dispatch_attention_threshold=1,
            queued_run_attention_threshold=1,
            unreviewed_proposal_attention_threshold=1,
            recent_non_success_attention_threshold=0,
            max_cycle_silence_seconds=300,
            failure_window_seconds=3600,
        ),
        as_of=base,
    )

    assert snapshot.signal is ContentSupplyHealthSignal.ATTENTION
    assert snapshot.reason_codes == tuple(sorted(snapshot.reason_codes))
    assert set(snapshot.reason_codes) == {
        "CONTENT_SUPPLY_CYCLE_SILENT",
        "INGESTION_RUN_BACKLOG",
        "LATEST_CONTENT_SUPPLY_CYCLE_NON_SUCCESS",
        "PROPOSAL_REVIEW_BACKLOG",
        "RECENT_CONTENT_SUPPLY_CYCLE_NON_SUCCESS",
        "RECENT_INGESTION_FAILURE",
        "RECENT_SOURCE_DISPATCH_NON_SUCCESS",
        "SOURCE_DISPATCH_BACKLOG",
    }


def test_running_cycle_suppresses_cycle_silence_attention() -> None:
    base = datetime(2026, 8, 2, 14, 0, tzinfo=UTC)
    snapshot = ContentSupplyHealthService(
        StaticFactsRepository(
            _facts(
                base,
                active_schedule_count=1,
                running_cycle_count=1,
            )
        )
    ).snapshot(ContentSupplyHealthPolicy(), as_of=base)

    assert snapshot.signal is ContentSupplyHealthSignal.NOMINAL
    assert "CONTENT_SUPPLY_CYCLE_SILENT" not in snapshot.reason_codes


def test_any_stale_ownership_signal_is_critical() -> None:
    base = datetime(2026, 8, 2, 15, 0, tzinfo=UTC)
    snapshot = ContentSupplyHealthService(
        StaticFactsRepository(
            _facts(
                base,
                stale_dispatch_count=1,
                stale_ingestion_lease_count=1,
                stale_cycle_count=1,
                pending_dispatch_count=1000,
            )
        )
    ).snapshot(ContentSupplyHealthPolicy(), as_of=base)

    assert snapshot.signal is ContentSupplyHealthSignal.CRITICAL
    assert set(snapshot.reason_codes) >= {
        "STALE_SOURCE_DISPATCH",
        "STALE_INGESTION_LEASE",
        "STALE_CONTENT_SUPPLY_CYCLE",
    }


def test_snapshot_operational_allowlist_is_exact() -> None:
    base = datetime(2026, 8, 2, 16, 0, tzinfo=UTC)
    snapshot = ContentSupplyHealthService(StaticFactsRepository(_facts(base))).snapshot(
        ContentSupplyHealthPolicy(),
        as_of=base,
    )
    operational = snapshot.as_operational_dict()

    assert set(operational) == {
        "signal",
        "as_of",
        "reason_codes",
        "active_schedule_count",
        "paused_schedule_count",
        "due_schedule_count",
        "pending_dispatch_count",
        "running_dispatch_count",
        "stale_dispatch_count",
        "recent_dispatch_non_success_count",
        "queued_ingestion_run_count",
        "running_ingestion_run_count",
        "stale_ingestion_lease_count",
        "recent_failed_ingestion_run_count",
        "unreviewed_proposal_count",
        "running_cycle_count",
        "stale_cycle_count",
        "recent_non_success_cycle_count",
        "latest_terminal_cycle_state",
        "latest_terminal_cycle_completed_at",
        "seconds_since_latest_terminal_cycle",
    }
    assert not {
        "external_locator",
        "raw_storage_ref",
        "provider_response",
        "proposal_payload",
        "credential",
        "user_id",
        "title",
        "reviewer_ref",
    }.intersection(operational)


def test_memory_repository_reads_live_aggregate_counts() -> None:
    base = datetime(2026, 8, 2, 17, 0, tzinfo=UTC)
    scheduler = InMemorySourceAcquisitionSchedulerRepository()
    ingestion = InMemoryIngestionOrchestrationRepository()
    leases = InMemoryIngestionRunLeaseRepository(ingestion)
    cycles = InMemoryContentSupplyCycleRepository()

    active_schedule = SourceAcquisitionSchedule(
        id=uuid4(),
        schedule_key="active-schedule-key",
        adapter_code="test.health.v1",
        external_locator="https://private.example/source",
        pipeline_code="HEALTH_PIPELINE",
        pipeline_version="1.0.0",
        configuration_hash="sha256:health",
        interval_seconds=300,
        max_dispatch_attempts=3,
        state=SourceAcquisitionScheduleState.ACTIVE,
        next_due_at=base - timedelta(minutes=1),
        created_at=base - timedelta(hours=1),
        updated_at=base - timedelta(hours=1),
    )
    paused_schedule = SourceAcquisitionSchedule(
        id=uuid4(),
        schedule_key="paused-schedule-key",
        adapter_code="test.health.v1",
        external_locator="https://private.example/paused",
        pipeline_code="HEALTH_PIPELINE",
        pipeline_version="1.0.0",
        configuration_hash="sha256:health-paused",
        interval_seconds=300,
        max_dispatch_attempts=3,
        state=SourceAcquisitionScheduleState.PAUSED,
        next_due_at=base,
        created_at=base - timedelta(hours=1),
        updated_at=base - timedelta(hours=1),
    )
    scheduler.create_or_get_schedule(active_schedule)
    scheduler.create_or_get_schedule(paused_schedule)
    pending = scheduler.plan_due_once(at=base - timedelta(minutes=1))
    assert pending is not None
    stale_dispatch = SourceAcquisitionDispatch(
        id=uuid4(),
        schedule_id=active_schedule.id,
        due_at=base - timedelta(minutes=10),
        state=SourceAcquisitionDispatchState.RUNNING,
        attempt_count=1,
        worker_ref="stale-dispatch-worker",
        claimed_at=base - timedelta(minutes=5),
        heartbeat_at=base - timedelta(minutes=4),
        expires_at=base - timedelta(minutes=3),
        created_at=base - timedelta(minutes=10),
        updated_at=base - timedelta(minutes=4),
    )
    failed_dispatch = SourceAcquisitionDispatch(
        id=uuid4(),
        schedule_id=active_schedule.id,
        due_at=base - timedelta(minutes=20),
        state=SourceAcquisitionDispatchState.FINAL_FAILURE,
        attempt_count=1,
        completed_at=base - timedelta(minutes=2),
        error_code="BOUNDED_FAILURE",
        created_at=base - timedelta(minutes=20),
        updated_at=base - timedelta(minutes=2),
    )
    with scheduler._lock:
        scheduler._dispatches[stale_dispatch.id] = stale_dispatch
        scheduler._dispatches[failed_dispatch.id] = failed_dispatch

    queued_run = IngestionRun(
        id=uuid4(),
        run_key="queued-run-key",
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash="sha256:queued",
        pipeline_code="HEALTH_PIPELINE",
        pipeline_version="1.0.0",
        configuration_hash="sha256:health",
        state=IngestionRunState.QUEUED,
        created_at=base - timedelta(minutes=5),
        updated_at=base - timedelta(minutes=5),
    )
    failed_run = IngestionRun(
        id=uuid4(),
        run_key="failed-run-key",
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash="sha256:failed",
        pipeline_code="HEALTH_PIPELINE",
        pipeline_version="1.0.0",
        configuration_hash="sha256:health",
        state=IngestionRunState.FAILED_FINAL,
        created_at=base - timedelta(minutes=4),
        updated_at=base - timedelta(minutes=1),
    )
    ingestion.create_or_get_run(queued_run)
    ingestion.create_or_get_run(failed_run)
    stale_lease = IngestionRunLease(
        id=uuid4(),
        run_id=queued_run.id,
        worker_ref="stale-run-worker",
        state=IngestionRunLeaseState.ACTIVE,
        claimed_at=base - timedelta(minutes=4),
        heartbeat_at=base - timedelta(minutes=3),
        expires_at=base - timedelta(minutes=2),
    )
    with ingestion._lock:
        leases._leases[stale_lease.id] = stale_lease
        leases._active_by_run[queued_run.id] = stale_lease.id
        payload = {"secret": "not exposed"}
        proposal = Proposal(
            id=uuid4(),
            proposal_kind="QUESTION_DRAFT",
            payload_schema_ref="kefe.question",
            payload_schema_version="1.0.0",
            payload=payload,
            payload_hash=stable_payload_hash(payload),
            run_id=queued_run.id,
            stage_execution_id=uuid4(),
            created_at=base - timedelta(minutes=1),
        )
        ingestion._proposals[proposal.id] = proposal

    stale_cycle = ContentSupplyCycle(
        id=uuid4(),
        worker_ref="stale-cycle-worker",
        plan_hash="cycle-plan-stale",
        state=ContentSupplyCycleState.RUNNING,
        counters=ContentSupplyCycleCounters(),
        started_at=base - timedelta(minutes=10),
        heartbeat_at=base - timedelta(minutes=5),
        expires_at=base - timedelta(minutes=4),
    )
    degraded_cycle = ContentSupplyCycle(
        id=uuid4(),
        worker_ref="terminal-cycle-worker",
        plan_hash="cycle-plan-terminal",
        state=ContentSupplyCycleState.DEGRADED,
        counters=ContentSupplyCycleCounters(dispatch_attempted_count=1, dispatch_non_success_count=1),
        started_at=base - timedelta(minutes=8),
        heartbeat_at=base - timedelta(minutes=7),
        expires_at=base + timedelta(minutes=1),
        completed_at=base - timedelta(seconds=30),
        error_code="CONTENT_SUPPLY_DELEGATED_NON_SUCCESS",
    )
    cycles.create(stale_cycle)
    cycles.create(degraded_cycle)

    repository = InMemoryContentSupplyOperationalFactsRepository(
        scheduler=scheduler,
        ingestion=ingestion,
        leases=leases,
        cycles=cycles,
    )
    facts = repository.read_facts(as_of=base, failure_window_seconds=3600)

    assert facts.active_schedule_count == 1
    assert facts.paused_schedule_count == 1
    assert facts.due_schedule_count == 0
    assert facts.pending_dispatch_count == 1
    assert facts.running_dispatch_count == 1
    assert facts.stale_dispatch_count == 1
    assert facts.recent_dispatch_non_success_count == 1
    assert facts.queued_ingestion_run_count == 1
    assert facts.stale_ingestion_lease_count == 1
    assert facts.recent_failed_ingestion_run_count == 1
    assert facts.unreviewed_proposal_count == 1
    assert facts.running_cycle_count == 1
    assert facts.stale_cycle_count == 1
    assert facts.recent_non_success_cycle_count == 1
    assert facts.latest_terminal_cycle_state == "DEGRADED"
    assert facts.latest_terminal_cycle_completed_at == base - timedelta(seconds=30)
