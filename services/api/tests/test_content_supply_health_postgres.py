from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text

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
from kefe_api.modules.content_supply_health.models import (
    ContentSupplyHealthPolicy,
    ContentSupplyHealthSignal,
)
from kefe_api.modules.content_supply_health.service import ContentSupplyHealthService
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRunState,
    InputArtifactKind,
    Proposal,
    StageExecution,
    StageOutcome,
    stable_payload_hash,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.models import SourceArtifact

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
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
        for cycle_id in cycle_ids:
            connection.execute(
                text("DELETE FROM ingestion.content_supply_cycle WHERE id = :id"),
                {"id": cycle_id},
            )
        for schedule_id in schedule_ids:
            connection.execute(
                text(
                    """
                    DELETE FROM knowledge.source_acquisition_dispatch
                    WHERE schedule_id = :id
                    """
                ),
                {"id": schedule_id},
            )
            connection.execute(
                text(
                    """
                    DELETE FROM knowledge.source_acquisition_schedule
                    WHERE id = :id
                    """
                ),
                {"id": schedule_id},
            )
        for run_id in run_ids:
            connection.execute(
                text(
                    """
                    DELETE FROM ingestion.proposal_review_decision
                    WHERE proposal_id IN (
                        SELECT id FROM ingestion.proposal WHERE run_id = :id
                    )
                    """
                ),
                {"id": run_id},
            )
            connection.execute(
                text("DELETE FROM ingestion.proposal WHERE run_id = :id"),
                {"id": run_id},
            )
            connection.execute(
                text("DELETE FROM ingestion.stage_execution WHERE run_id = :id"),
                {"id": run_id},
            )
            connection.execute(
                text("DELETE FROM ingestion.run_lease WHERE run_id = :id"),
                {"id": run_id},
            )
            connection.execute(
                text("DELETE FROM ingestion.ingestion_run WHERE id = :id"),
                {"id": run_id},
            )
        for artifact_id in artifact_ids:
            connection.execute(
                text("DELETE FROM knowledge.source_artifact WHERE id = :id"),
                {"id": artifact_id},
            )


def _seed_schedule_and_dispatch_facts(
    engine,
    *,
    as_of: datetime,
    suffix: str,
) -> tuple[list[UUID], UUID]:
    schedule_ids = [uuid4() for _ in range(5)]
    stale_dispatch_id = uuid4()
    pending_dispatch_id = uuid4()
    failed_dispatch_id = uuid4()
    with engine.begin() as connection:
        rows = (
            (schedule_ids[0], "ACTIVE", as_of + timedelta(minutes=4)),
            (schedule_ids[1], "ACTIVE", as_of + timedelta(minutes=4)),
            (schedule_ids[2], "ACTIVE", as_of + timedelta(minutes=4)),
            (schedule_ids[3], "ACTIVE", as_of - timedelta(seconds=1)),
            (schedule_ids[4], "PAUSED", as_of + timedelta(hours=1)),
        )
        for index, (schedule_id, state, next_due_at) in enumerate(rows):
            connection.execute(
                text(
                    """
                    INSERT INTO knowledge.source_acquisition_schedule (
                        id, schedule_key, adapter_code, external_locator,
                        pipeline_code, pipeline_version, configuration_hash,
                        taxonomy_version, methodology_version, locale,
                        jurisdiction_code, interval_seconds,
                        max_dispatch_attempts, state, next_due_at,
                        created_at, updated_at
                    ) VALUES (
                        :id, :schedule_key, :adapter_code, :external_locator,
                        'HEALTH_POSTGRES_PIPELINE', '1.0.0', :configuration_hash,
                        NULL, NULL, NULL, NULL, 300, 3, :state, :next_due_at,
                        :created_at, :updated_at
                    )
                    """
                ),
                {
                    "id": schedule_id,
                    "schedule_key": f"health-{suffix}-{index}",
                    "adapter_code": f"test.health_{suffix}_{index}.v1",
                    "external_locator": (
                        f"https://private.example/health/{suffix}/{index}"
                    ),
                    "configuration_hash": f"sha256:health:{suffix}:{index}",
                    "state": state,
                    "next_due_at": next_due_at,
                    "created_at": as_of - timedelta(hours=1),
                    "updated_at": as_of - timedelta(minutes=1),
                },
            )
        connection.execute(
            text(
                """
                INSERT INTO knowledge.source_acquisition_dispatch (
                    id, schedule_id, due_at, state, attempt_count,
                    worker_ref, claimed_at, heartbeat_at, expires_at,
                    completed_at, source_artifact_id, ingestion_run_id,
                    error_code, created_at, updated_at
                ) VALUES (
                    :id, :schedule_id, :due_at, 'RUNNING', 1,
                    'stale-health-dispatch-worker', :claimed_at,
                    :heartbeat_at, :expires_at, NULL, NULL, NULL, NULL,
                    :created_at, :updated_at
                )
                """
            ),
            {
                "id": stale_dispatch_id,
                "schedule_id": schedule_ids[0],
                "due_at": as_of - timedelta(minutes=5),
                "claimed_at": as_of - timedelta(seconds=30),
                "heartbeat_at": as_of - timedelta(seconds=20),
                "expires_at": as_of - timedelta(seconds=10),
                "created_at": as_of - timedelta(minutes=5),
                "updated_at": as_of - timedelta(seconds=20),
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO knowledge.source_acquisition_dispatch (
                    id, schedule_id, due_at, state, attempt_count,
                    worker_ref, claimed_at, heartbeat_at, expires_at,
                    completed_at, source_artifact_id, ingestion_run_id,
                    error_code, created_at, updated_at
                ) VALUES (
                    :id, :schedule_id, :due_at, 'PENDING', 0,
                    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                    :created_at, :updated_at
                )
                """
            ),
            {
                "id": pending_dispatch_id,
                "schedule_id": schedule_ids[1],
                "due_at": as_of - timedelta(minutes=4),
                "created_at": as_of - timedelta(minutes=4),
                "updated_at": as_of - timedelta(minutes=4),
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO knowledge.source_acquisition_dispatch (
                    id, schedule_id, due_at, state, attempt_count,
                    worker_ref, claimed_at, heartbeat_at, expires_at,
                    completed_at, source_artifact_id, ingestion_run_id,
                    error_code, created_at, updated_at
                ) VALUES (
                    :id, :schedule_id, :due_at, 'FINAL_FAILURE', 1,
                    NULL, NULL, NULL, NULL, :completed_at, NULL, NULL,
                    'HEALTH_TEST_FAILURE', :created_at, :updated_at
                )
                """
            ),
            {
                "id": failed_dispatch_id,
                "schedule_id": schedule_ids[2],
                "due_at": as_of - timedelta(minutes=3),
                "completed_at": as_of - timedelta(seconds=5),
                "created_at": as_of - timedelta(minutes=3),
                "updated_at": as_of - timedelta(seconds=5),
            },
        )
    return schedule_ids, stale_dispatch_id


def _seed_cycle_facts(
    engine,
    *,
    as_of: datetime,
    suffix: str,
) -> tuple[list[UUID], UUID]:
    stale_cycle_id = uuid4()
    terminal_cycle_id = uuid4()
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO ingestion.content_supply_cycle (
                    id, worker_ref, plan_hash, state,
                    planned_count, dispatch_attempted_count,
                    dispatch_succeeded_count, dispatch_non_success_count,
                    ingestion_attempted_count, ingestion_succeeded_count,
                    ingestion_non_success_count, started_at, heartbeat_at,
                    expires_at, completed_at, error_code
                ) VALUES (
                    :id, :worker_ref, :plan_hash, 'RUNNING',
                    0, 0, 0, 0, 0, 0, 0,
                    :started_at, :heartbeat_at, :expires_at, NULL, NULL
                )
                """
            ),
            {
                "id": stale_cycle_id,
                "worker_ref": f"stale-cycle-{suffix}",
                "plan_hash": f"plan-stale-{suffix}",
                "started_at": as_of - timedelta(minutes=2),
                "heartbeat_at": as_of - timedelta(seconds=20),
                "expires_at": as_of - timedelta(seconds=10),
            },
        )
        connection.execute(
            text(
                """
                INSERT INTO ingestion.content_supply_cycle (
                    id, worker_ref, plan_hash, state,
                    planned_count, dispatch_attempted_count,
                    dispatch_succeeded_count, dispatch_non_success_count,
                    ingestion_attempted_count, ingestion_succeeded_count,
                    ingestion_non_success_count, started_at, heartbeat_at,
                    expires_at, completed_at, error_code
                ) VALUES (
                    :id, :worker_ref, :plan_hash, 'DEGRADED',
                    0, 1, 0, 1, 0, 0, 0,
                    :started_at, :heartbeat_at, :expires_at,
                    :completed_at, 'CONTENT_SUPPLY_DELEGATED_NON_SUCCESS'
                )
                """
            ),
            {
                "id": terminal_cycle_id,
                "worker_ref": f"terminal-cycle-{suffix}",
                "plan_hash": f"plan-terminal-{suffix}",
                "started_at": as_of - timedelta(minutes=1),
                "heartbeat_at": as_of - timedelta(seconds=30),
                "expires_at": as_of + timedelta(minutes=9),
                "completed_at": as_of,
            },
        )
    return [stale_cycle_id, terminal_cycle_id], stale_cycle_id


def test_postgres_snapshot_reads_repeatable_aggregate_deltas_without_mutation() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    as_of = datetime.now(UTC) + timedelta(seconds=5)
    suffix = uuid4().hex[:10]
    pipeline_code = f"HEALTH_POSTGRES_PIPELINE_{suffix}"
    facts_repository = PostgresContentSupplyOperationalFactsRepository(engine)
    baseline = facts_repository.read_facts(as_of=as_of, failure_window_seconds=3600)

    knowledge_repository = PostgresKnowledgeRepository(engine)
    ingestion_repository = PostgresIngestionOrchestrationRepository(engine)
    ingestion_service = IngestionOrchestrationService(ingestion_repository)
    lease_repository = PostgresIngestionRunLeaseRepository(engine)

    schedule_ids: list[UUID] = []
    cycle_ids: list[UUID] = []
    run_ids: list[UUID] = []
    artifact_ids: list[UUID] = []
    try:
        schedule_ids, stale_dispatch_id = _seed_schedule_and_dispatch_facts(
            engine,
            as_of=as_of,
            suffix=suffix,
        )
        cycle_ids, stale_cycle_id = _seed_cycle_facts(
            engine,
            as_of=as_of,
            suffix=suffix,
        )

        artifacts = tuple(
            knowledge_repository.add_source_artifact(
                SourceArtifact.create(
                    adapter_code=f"test.health_artifact_{suffix}_{index}.v1",
                    external_locator=(
                        f"https://private.example/artifact/{suffix}/{index}"
                    ),
                    content_hash=f"sha256:{suffix}:{index}",
                    captured_at=as_of - timedelta(minutes=5),
                    raw_storage_ref=f"secret://health/{suffix}/{index}",
                )
            )
            for index in range(3)
        )
        artifact_ids.extend(artifact.id for artifact in artifacts)

        stale_run = ingestion_service.start_run(
            input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
            input_artifact_id=artifacts[0].id,
            input_content_hash=artifacts[0].content_hash,
            pipeline_code=pipeline_code,
            pipeline_version="1.0.0",
            configuration_hash=f"sha256:run:{suffix}:stale",
        )
        run_ids.append(stale_run.id)
        claimed = lease_repository.claim_next(
            worker_ref="stale-health-run-worker",
            claimed_at=as_of - timedelta(seconds=20),
            expires_at=as_of - timedelta(seconds=10),
            pipeline_code=pipeline_code,
            pipeline_version="1.0.0",
        )
        assert claimed is not None and claimed.run.id == stale_run.id

        queued_run = ingestion_service.start_run(
            input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
            input_artifact_id=artifacts[1].id,
            input_content_hash=artifacts[1].content_hash,
            pipeline_code=pipeline_code,
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
            input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
            input_artifact_id=artifacts[2].id,
            input_content_hash=artifacts[2].content_hash,
            pipeline_code=pipeline_code,
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
                {"id": stale_dispatch_id},
            ).scalar_one()
            cycle_state = connection.execute(
                text(
                    """
                    SELECT state
                    FROM ingestion.content_supply_cycle
                    WHERE id = :id
                    """
                ),
                {"id": stale_cycle_id},
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
