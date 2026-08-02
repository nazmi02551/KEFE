from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_content_supply_cycle import (
    PostgresContentSupplyCycleRepository,
)
from kefe_api.infrastructure.postgres_content_supply_health import (
    PostgresContentSupplyOperationalFactsRepository,
)
from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_ingestion_run_leases import (
    PostgresIngestionRunLeaseRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.infrastructure.postgres_source_acquisition_scheduler import (
    PostgresSourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.content_supply_cycle.models import (
    ContentSupplyCycle,
    ContentSupplyCycleCommand,
    ContentSupplyCycleCounters,
    ContentSupplyCycleState,
)
from kefe_api.modules.content_supply_health.models import (
    ContentSupplyHealthPolicy,
    ContentSupplyHealthSignal,
)
from kefe_api.modules.content_supply_health.service import ContentSupplyHealthService
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRunState,
    Proposal,
    StageExecution,
    StageOutcome,
    stable_payload_hash,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionDispatchState,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    NoOpSourceDispatchObserver,
    SourceAcquisitionSchedulerService,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


class UnusedAcquisitionService:
    def acquire(self, *args, **kwargs):
        del args, kwargs
        raise AssertionError("health snapshot setup must not execute acquisition")


def _create_schedule(
    service: SourceAcquisitionSchedulerService,
    *,
    adapter_code: str,
    locator: str,
    first_due_at: datetime,
):
    return service.create_schedule(
        adapter_code=adapter_code,
        external_locator=locator,
        pipeline_code="HEALTH_POSTGRES_PIPELINE",
        pipeline_version="1.0.0",
        configuration_hash=f"sha256:{uuid4().hex}",
        first_due_at=first_due_at,
        interval_seconds=300,
        max_dispatch_attempts=3,
        now=first_due_at - timedelta(minutes=1),
    )


def _cleanup(
    engine,
    *,
    schedule_ids: list[UUID],
    cycle_ids: list[UUID],
    run_ids: list[UUID],
    artifact_ids: list[UUID],
) -> None:
    with engine.begin() as connection:
        if cycle_ids:
            connection.execute(
                text("DELETE FROM ingestion.content_supply_cycle WHERE id = ANY(:ids)"),
                {"ids": cycle_ids},
            )
        if schedule_ids:
            connection.execute(
                text(
                    """
                    DELETE FROM knowledge.source_acquisition_dispatch
                    WHERE schedule_id = ANY(:ids)
                    """
                ),
                {"ids": schedule_ids},
            )
            connection.execute(
                text(
                    """
                    DELETE FROM knowledge.source_acquisition_schedule
                    WHERE id = ANY(:ids)
                    """
                ),
                {"ids": schedule_ids},
            )
        if run_ids:
            connection.execute(
                text(
                    """
                    DELETE FROM ingestion.proposal_review_decision
                    WHERE proposal_id IN (
                        SELECT id FROM ingestion.proposal WHERE run_id = ANY(:ids)
                    )
                    """
                ),
                {"ids": run_ids},
            )
            connection.execute(
                text("DELETE FROM ingestion.proposal WHERE run_id = ANY(:ids)"),
                {"ids": run_ids},
            )
            connection.execute(
                text("DELETE FROM ingestion.stage_execution WHERE run_id = ANY(:ids)"),
                {"ids": run_ids},
            )
            connection.execute(
                text("DELETE FROM ingestion.run_lease WHERE run_id = ANY(:ids)"),
                {"ids": run_ids},
            )
            connection.execute(
                text("DELETE FROM ingestion.ingestion_run WHERE id = ANY(:ids)"),
                {"ids": run_ids},
            )
        if artifact_ids:
            connection.execute(
                text("DELETE FROM knowledge.source_artifact WHERE id = ANY(:ids)"),
                {"ids": artifact_ids},
            )


def test_postgres_snapshot_reads_repeatable_aggregate_deltas_without_mutation() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    as_of = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid4().hex[:10]
    facts_repository = PostgresContentSupplyOperationalFactsRepository(engine)
    baseline = facts_repository.read_facts(as_of=as_of, failure_window_seconds=3600)

    scheduler_repository = PostgresSourceAcquisitionSchedulerRepository(engine)
    scheduler_service = SourceAcquisitionSchedulerService(
        repository=scheduler_repository,
        acquisition=UnusedAcquisitionService(),
        observer=NoOpSourceDispatchObserver(),
        clock=lambda: as_of,
    )
    knowledge_repository = PostgresKnowledgeRepository(engine)
    ingestion_repository = PostgresIngestionOrchestrationRepository(engine)
    ingestion_service = IngestionOrchestrationService(ingestion_repository)
    lease_repository = PostgresIngestionRunLeaseRepository(engine)
    cycle_repository = PostgresContentSupplyCycleRepository(engine)

    schedule_ids: list[UUID] = []
    cycle_ids: list[UUID] = []
    run_ids: list[UUID] = []
    artifact_ids: list[UUID] = []
    try:
        running_schedule = _create_schedule(
            scheduler_service,
            adapter_code=f"test.health_running_{suffix}.v1",
            locator=f"https://private.example/running/{suffix}",
            first_due_at=as_of - timedelta(minutes=1),
        )
        schedule_ids.append(running_schedule.id)
        running_dispatch = scheduler_service.plan_due_once(
            now=as_of - timedelta(minutes=1)
        )
        assert running_dispatch is not None
        scheduler_repository.claim_pending_once(
            worker_ref="stale-health-dispatch-worker",
            claimed_at=as_of - timedelta(seconds=20),
            expires_at=as_of - timedelta(seconds=10),
        )

        pending_schedule = _create_schedule(
            scheduler_service,
            adapter_code=f"test.health_pending_{suffix}.v1",
            locator=f"https://private.example/pending/{suffix}",
            first_due_at=as_of - timedelta(minutes=1),
        )
        schedule_ids.append(pending_schedule.id)
        assert scheduler_service.plan_due_once(
            now=as_of - timedelta(minutes=1)
        ) is not None

        failed_schedule = _create_schedule(
            scheduler_service,
            adapter_code=f"test.health_failed_{suffix}.v1",
            locator=f"https://private.example/failed/{suffix}",
            first_due_at=as_of - timedelta(minutes=1),
        )
        schedule_ids.append(failed_schedule.id)
        failed_dispatch = scheduler_service.plan_due_once(
            now=as_of - timedelta(minutes=1)
        )
        assert failed_dispatch is not None
        failed_claim = scheduler_repository.claim_pending_once(
            worker_ref="failed-health-dispatch-worker",
            claimed_at=as_of - timedelta(seconds=20),
            expires_at=as_of + timedelta(seconds=20),
        )
        assert failed_claim is not None
        scheduler_repository.complete(
            dispatch_id=failed_claim.dispatch.id,
            worker_ref="failed-health-dispatch-worker",
            completed_at=as_of - timedelta(seconds=5),
            target_state=SourceAcquisitionDispatchState.FINAL_FAILURE,
            error_code="HEALTH_TEST_FAILURE",
        )

        due_schedule = _create_schedule(
            scheduler_service,
            adapter_code=f"test.health_due_{suffix}.v1",
            locator=f"https://private.example/due/{suffix}",
            first_due_at=as_of - timedelta(seconds=1),
        )
        schedule_ids.append(due_schedule.id)
        paused_schedule = _create_schedule(
            scheduler_service,
            adapter_code=f"test.health_paused_{suffix}.v1",
            locator=f"https://private.example/paused/{suffix}",
            first_due_at=as_of + timedelta(hours=1),
        )
        schedule_ids.append(paused_schedule.id)
        scheduler_service.pause(paused_schedule.id, now=as_of)

        artifacts = tuple(
            knowledge_repository.add_source_artifact(
                SourceArtifact.create(
                    adapter_code=f"test.health_artifact_{suffix}_{index}.v1",
                    external_locator=f"https://private.example/artifact/{suffix}/{index}",
                    content_hash=f"sha256:{suffix}:{index}",
                    captured_at=as_of - timedelta(minutes=5),
                    raw_storage_ref=f"secret://health/{suffix}/{index}",
                )
            )
            for index in range(3)
        )
        artifact_ids.extend(artifact.id for artifact in artifacts)

        stale_run = ingestion_service.start_run(
            input_artifact_kind="SOURCE_ARTIFACT",
            input_artifact_id=artifacts[0].id,
            input_content_hash=artifacts[0].content_hash,
            pipeline_code="HEALTH_POSTGRES_PIPELINE",
            pipeline_version="1.0.0",
            configuration_hash=f"sha256:run:{suffix}:stale",
        )
        run_ids.append(stale_run.id)
        lease_repository.claim_next(
            worker_ref="stale-health-run-worker",
            claimed_at=as_of - timedelta(seconds=20),
            expires_at=as_of - timedelta(seconds=10),
            pipeline_code="HEALTH_POSTGRES_PIPELINE",
            pipeline_version="1.0.0",
        )

        queued_run = ingestion_service.start_run(
            input_artifact_kind="SOURCE_ARTIFACT",
            input_artifact_id=artifacts[1].id,
            input_content_hash=artifacts[1].content_hash,
            pipeline_code="HEALTH_POSTGRES_PIPELINE",
            pipeline_version="1.0.0",
            configuration_hash=f"sha256:run:{suffix}:queued",
        )
        run_ids.append(queued_run.id)
        stage = StageExecution(
            id=uuid4(),
            run_id=queued_run.id,
            stage_code="HEALTH_STAGE",
            stage_version="1.0.0",
            attempt_no=1,
            max_attempts=1,
            executor_kind=ExecutorKind.DETERMINISTIC,
            input_hash="sha256:stage-input",
            output_hash="sha256:stage-output",
            started_at=as_of - timedelta(minutes=2),
            completed_at=as_of - timedelta(minutes=1),
            outcome=StageOutcome.SUCCEEDED,
        )
        ingestion_repository.add_stage_execution(stage)
        payload = {"secret": "never expose"}
        ingestion_repository.add_proposal(
            Proposal(
                id=uuid4(),
                proposal_kind="QUESTION_DRAFT",
                payload_schema_ref="kefe.question",
                payload_schema_version="1.0.0",
                payload=payload,
                payload_hash=stable_payload_hash(payload),
                run_id=queued_run.id,
                stage_execution_id=stage.id,
                created_at=as_of - timedelta(seconds=30),
            )
        )

        failed_run = ingestion_service.start_run(
            input_artifact_kind="SOURCE_ARTIFACT",
            input_artifact_id=artifacts[2].id,
            input_content_hash=artifacts[2].content_hash,
            pipeline_code="HEALTH_POSTGRES_PIPELINE",
            pipeline_version="1.0.0",
            configuration_hash=f"sha256:run:{suffix}:failed",
        )
        run_ids.append(failed_run.id)
        running_failed = failed_run.transition(
            IngestionRunState.RUNNING,
            at=as_of - timedelta(seconds=20),
        )
        ingestion_repository.update_run(running_failed)
        ingestion_repository.update_run(
            running_failed.transition(
                IngestionRunState.FAILED_FINAL,
                at=as_of - timedelta(seconds=5),
            )
        )

        cycle_command = ContentSupplyCycleCommand(
            worker_ref=f"health-cycle-{suffix}",
            plan_budget=0,
            dispatch_budget=0,
            pipeline_targets=(),
            cycle_ttl_seconds=60,
            dispatch_ttl_seconds=60,
            ingestion_ttl_seconds=60,
        )
        stale_cycle = cycle_repository.create(
            ContentSupplyCycle.start(
                cycle_command,
                started_at=as_of - timedelta(minutes=2),
                expires_at=as_of - timedelta(seconds=10),
            )
        )
        cycle_ids.append(stale_cycle.id)
        terminal_cycle = cycle_repository.create(
            ContentSupplyCycle.start(
                ContentSupplyCycleCommand(
                    worker_ref=f"terminal-health-cycle-{suffix}",
                    plan_budget=0,
                    dispatch_budget=0,
                    pipeline_targets=(),
                    cycle_ttl_seconds=600,
                    dispatch_ttl_seconds=60,
                    ingestion_ttl_seconds=60,
                ),
                started_at=as_of - timedelta(minutes=1),
                expires_at=as_of + timedelta(minutes=9),
            )
        )
        cycle_ids.append(terminal_cycle.id)
        cycle_repository.complete(
            cycle_id=terminal_cycle.id,
            worker_ref=terminal_cycle.worker_ref,
            completed_at=as_of,
            state=ContentSupplyCycleState.DEGRADED,
            counters=ContentSupplyCycleCounters(
                dispatch_attempted_count=1,
                dispatch_non_success_count=1,
            ),
            error_code="CONTENT_SUPPLY_DELEGATED_NON_SUCCESS",
        )

        snapshot = ContentSupplyHealthService(facts_repository).snapshot(
            ContentSupplyHealthPolicy(
                pending_dispatch_attention_threshold=0,
                queued_run_attention_threshold=0,
                unreviewed_proposal_attention_threshold=0,
                recent_non_success_attention_threshold=0,
                max_cycle_silence_seconds=60,
                failure_window_seconds=3600,
            ),
            as_of=as_of,
        )
        after = facts_repository.read_facts(
            as_of=as_of,
            failure_window_seconds=3600,
        )

        assert after.active_schedule_count == baseline.active_schedule_count + 4
        assert after.paused_schedule_count == baseline.paused_schedule_count + 1
        assert after.due_schedule_count == baseline.due_schedule_count + 1
        assert after.pending_dispatch_count == baseline.pending_dispatch_count + 1
        assert after.running_dispatch_count == baseline.running_dispatch_count + 1
        assert after.stale_dispatch_count == baseline.stale_dispatch_count + 1
        assert after.recent_dispatch_non_success_count == (
            baseline.recent_dispatch_non_success_count + 1
        )
        assert after.queued_ingestion_run_count == (
            baseline.queued_ingestion_run_count + 1
        )
        assert after.running_ingestion_run_count == (
            baseline.running_ingestion_run_count + 1
        )
        assert after.stale_ingestion_lease_count == (
            baseline.stale_ingestion_lease_count + 1
        )
        assert after.recent_failed_ingestion_run_count == (
            baseline.recent_failed_ingestion_run_count + 1
        )
        assert after.unreviewed_proposal_count == (
            baseline.unreviewed_proposal_count + 1
        )
        assert after.running_cycle_count == baseline.running_cycle_count + 1
        assert after.stale_cycle_count == baseline.stale_cycle_count + 1
        assert after.recent_non_success_cycle_count == (
            baseline.recent_non_success_cycle_count + 1
        )
        assert after.latest_terminal_cycle_state == "DEGRADED"
        assert after.latest_terminal_cycle_completed_at == as_of
        assert snapshot.signal is ContentSupplyHealthSignal.CRITICAL
        assert "secret://health" not in repr(snapshot.as_operational_dict())

        with engine.connect() as connection:
            dispatch_state = connection.execute(
                text(
                    """
                    SELECT state
                    FROM knowledge.source_acquisition_dispatch
                    WHERE id = :id
                    """
                ),
                {"id": running_dispatch.id},
            ).scalar_one()
            cycle_state = connection.execute(
                text(
                    """
                    SELECT state
                    FROM ingestion.content_supply_cycle
                    WHERE id = :id
                    """
                ),
                {"id": stale_cycle.id},
            ).scalar_one()
        assert dispatch_state == "RUNNING"
        assert cycle_state == "RUNNING"
    finally:
        _cleanup(
            engine,
            schedule_ids=schedule_ids,
            cycle_ids=cycle_ids,
            run_ids=run_ids,
            artifact_ids=artifact_ids,
        )
