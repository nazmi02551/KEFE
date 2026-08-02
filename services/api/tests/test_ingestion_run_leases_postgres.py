from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_ingestion_run_leases import (
    PostgresIngestionRunLeaseRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.modules.ingestion_orchestration.lease_service import (
    IngestionRunLeaseError,
    IngestionRunLeaseService,
)
from kefe_api.modules.ingestion_orchestration.leases import (
    IngestionRunLeaseReleaseDisposition,
    IngestionRunLeaseState,
)
from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRunState,
    InputArtifactKind,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.models import SourceArtifact

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _seed_run(database_url: str, pipeline_code: str):
    engine = create_engine(database_url)
    source = PostgresKnowledgeRepository(engine).add_source_artifact(
        SourceArtifact.create(
            adapter_code="ingestion-worker-lease-fixture",
            external_locator=f"https://example.test/worker-lease/{uuid4()}",
            content_hash=f"sha256:worker-lease-{uuid4()}",
            language_code="en",
        )
    )
    service = IngestionOrchestrationService(
        PostgresIngestionOrchestrationRepository(engine)
    )
    return service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=source.id,
        input_content_hash=source.content_hash,
        pipeline_code=pipeline_code,
        pipeline_version="1.0.0",
        configuration_hash="sha256:worker-lease-config",
    )


def _state(database_url: str, run_id: UUID) -> str:
    engine = create_engine(database_url)
    with engine.connect() as connection:
        return connection.execute(
            text("SELECT state FROM ingestion.ingestion_run WHERE id = :run_id"),
            {"run_id": run_id},
        ).scalar_one()


def test_postgres_concurrent_claimers_never_receive_same_run() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    pipeline_code = f"LEASE_CONCURRENCY_{uuid4().hex[:10]}"
    run = _seed_run(database_url, pipeline_code)
    barrier = Barrier(2)
    now = datetime.now(UTC)

    def claim(worker_ref: str):
        service = IngestionRunLeaseService(
            PostgresIngestionRunLeaseRepository(create_engine(database_url))
        )
        barrier.wait()
        return service.claim_next(
            worker_ref=worker_ref,
            ttl_seconds=60,
            pipeline_code=pipeline_code,
            now=now,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(claim, ("worker-a", "worker-b")))

    claimed = [result for result in results if result is not None]
    assert len(claimed) == 1
    assert claimed[0].run.id == run.id
    assert _state(database_url, run.id) == IngestionRunState.RUNNING.value

    engine = create_engine(database_url)
    with engine.connect() as connection:
        active_count = connection.execute(
            text(
                """
                SELECT count(*) FROM ingestion.run_lease
                WHERE run_id = :run_id AND state = 'ACTIVE'
                """
            ),
            {"run_id": run.id},
        ).scalar_one()
    assert active_count == 1


def test_postgres_heartbeat_expiry_recovery_and_reclaim() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    pipeline_code = f"LEASE_RECOVERY_{uuid4().hex[:10]}"
    run = _seed_run(database_url, pipeline_code)
    repository = PostgresIngestionRunLeaseRepository(create_engine(database_url))
    service = IngestionRunLeaseService(repository)
    base = datetime.now(UTC)

    first = service.claim_next(
        worker_ref="worker-a",
        ttl_seconds=5,
        pipeline_code=pipeline_code,
        now=base,
    )
    assert first is not None

    with pytest.raises(IngestionRunLeaseError) as wrong_owner:
        service.heartbeat(
            lease_id=first.lease.id,
            worker_ref="worker-b",
            ttl_seconds=30,
            now=base + timedelta(seconds=1),
        )
    assert wrong_owner.value.code == "INGESTION_RUN_LEASE_NOT_ACTIVE"

    heartbeat = service.heartbeat(
        lease_id=first.lease.id,
        worker_ref="worker-a",
        ttl_seconds=5,
        now=base + timedelta(seconds=2),
    )
    assert heartbeat.expires_at == base + timedelta(seconds=7)

    recovered = service.recover_expired(now=base + timedelta(seconds=8))
    assert [item.id for item in recovered] == [first.lease.id]
    assert recovered[0].state is IngestionRunLeaseState.EXPIRED
    assert _state(database_url, run.id) == IngestionRunState.QUEUED.value

    with pytest.raises(IngestionRunLeaseError):
        service.assert_active(
            lease_id=first.lease.id,
            worker_ref="worker-a",
            now=base + timedelta(seconds=8),
        )

    second = service.claim_next(
        worker_ref="worker-c",
        ttl_seconds=60,
        pipeline_code=pipeline_code,
        now=base + timedelta(seconds=9),
    )
    assert second is not None
    assert second.run.id == run.id
    assert second.lease.id != first.lease.id
    assert repository.get_lease(first.lease.id).state is IngestionRunLeaseState.EXPIRED
    assert repository.get_lease(second.lease.id).state is IngestionRunLeaseState.ACTIVE


def test_postgres_release_rules_requeue_and_terminal_history() -> None:
    database_url = os.environ["KEFE_DATABASE_URL"]
    pipeline_code = f"LEASE_RELEASE_{uuid4().hex[:10]}"
    run = _seed_run(database_url, pipeline_code)
    engine = create_engine(database_url)
    service = IngestionRunLeaseService(PostgresIngestionRunLeaseRepository(engine))
    base = datetime.now(UTC)

    first = service.claim_next(
        worker_ref="worker-a",
        ttl_seconds=60,
        pipeline_code=pipeline_code,
        now=base,
    )
    assert first is not None
    with pytest.raises(IngestionRunLeaseError) as invalid_terminal:
        service.release(
            lease_id=first.lease.id,
            worker_ref="worker-a",
            disposition=IngestionRunLeaseReleaseDisposition.TERMINAL,
            now=base + timedelta(seconds=1),
        )
    assert invalid_terminal.value.code == "INGESTION_RUN_LEASE_RELEASE_INVALID"

    requeued = service.release(
        lease_id=first.lease.id,
        worker_ref="worker-a",
        disposition=IngestionRunLeaseReleaseDisposition.REQUEUE,
        now=base + timedelta(seconds=2),
    )
    assert requeued.state is IngestionRunLeaseState.RELEASED
    assert _state(database_url, run.id) == IngestionRunState.QUEUED.value

    second = service.claim_next(
        worker_ref="worker-b",
        ttl_seconds=60,
        pipeline_code=pipeline_code,
        now=base + timedelta(seconds=3),
    )
    assert second is not None
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE ingestion.ingestion_run
                SET state = 'SUCCEEDED', updated_at = :updated_at
                WHERE id = :run_id
                """
            ),
            {"run_id": run.id, "updated_at": base + timedelta(seconds=4)},
        )
    terminal = service.release(
        lease_id=second.lease.id,
        worker_ref="worker-b",
        disposition=IngestionRunLeaseReleaseDisposition.TERMINAL,
        now=base + timedelta(seconds=5),
    )
    assert terminal.state is IngestionRunLeaseState.RELEASED
    assert terminal.release_disposition is IngestionRunLeaseReleaseDisposition.TERMINAL
    assert _state(database_url, run.id) == IngestionRunState.SUCCEEDED.value

    with engine.connect() as connection:
        history = connection.execute(
            text(
                """
                SELECT state, release_disposition
                FROM ingestion.run_lease
                WHERE run_id = :run_id
                ORDER BY claimed_at, id
                """
            ),
            {"run_id": run.id},
        ).all()
    assert history == [
        ("RELEASED", "REQUEUE"),
        ("RELEASED", "TERMINAL"),
    ]
