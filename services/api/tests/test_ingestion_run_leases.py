from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.in_memory_leases import (
    InMemoryIngestionRunLeaseRepository,
)
from kefe_api.modules.ingestion_orchestration.lease_service import (
    IngestionRunLeaseError,
    IngestionRunLeaseService,
)
from kefe_api.modules.ingestion_orchestration.leases import (
    IngestionRunLeaseReleaseDisposition,
    IngestionRunLeaseState,
)
from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    IngestionRunState,
    InputArtifactKind,
)


def _run(
    repository: InMemoryIngestionOrchestrationRepository,
    *,
    index: int,
    updated_at: datetime,
    pipeline_code: str = "LEASE_PIPELINE",
) -> IngestionRun:
    run = IngestionRun(
        id=uuid4(),
        run_key=f"lease-run-{index}-{uuid4()}",
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash=f"sha256:lease-source-{index}",
        pipeline_code=pipeline_code,
        pipeline_version="1.0.0",
        configuration_hash="sha256:lease-config",
        state=IngestionRunState.QUEUED,
        created_at=updated_at,
        updated_at=updated_at,
    )
    return repository.create_or_get_run(run)


def _services():
    ingestion = InMemoryIngestionOrchestrationRepository()
    lease_repository = InMemoryIngestionRunLeaseRepository(ingestion)
    return ingestion, lease_repository, IngestionRunLeaseService(lease_repository)


def test_memory_claim_is_oldest_first_exclusive_and_pipeline_filtered() -> None:
    ingestion, _, leases = _services()
    base = datetime(2026, 8, 2, 5, 0, tzinfo=UTC)
    oldest = _run(ingestion, index=1, updated_at=base)
    other_pipeline = _run(
        ingestion,
        index=2,
        updated_at=base + timedelta(seconds=1),
        pipeline_code="OTHER_PIPELINE",
    )
    newest = _run(ingestion, index=3, updated_at=base + timedelta(seconds=2))

    first = leases.claim_next(
        worker_ref="worker-a",
        ttl_seconds=30,
        pipeline_code="LEASE_PIPELINE",
        now=base + timedelta(minutes=1),
    )
    second = leases.claim_next(
        worker_ref="worker-b",
        ttl_seconds=30,
        pipeline_code="LEASE_PIPELINE",
        now=base + timedelta(minutes=1),
    )
    none_left = leases.claim_next(
        worker_ref="worker-c",
        ttl_seconds=30,
        pipeline_code="LEASE_PIPELINE",
        now=base + timedelta(minutes=1),
    )

    assert first is not None and first.run.id == oldest.id
    assert second is not None and second.run.id == newest.id
    assert first.lease.id != second.lease.id
    assert none_left is None
    assert ingestion.get_run(oldest.id).state is IngestionRunState.RUNNING
    assert ingestion.get_run(newest.id).state is IngestionRunState.RUNNING
    assert ingestion.get_run(other_pipeline.id).state is IngestionRunState.QUEUED


def test_memory_heartbeat_requires_exact_owner_and_extends_expiry() -> None:
    ingestion, _, leases = _services()
    base = datetime(2026, 8, 2, 6, 0, tzinfo=UTC)
    _run(ingestion, index=1, updated_at=base)
    claim = leases.claim_next(
        worker_ref="worker-a",
        ttl_seconds=10,
        now=base + timedelta(seconds=1),
    )
    assert claim is not None

    with pytest.raises(IngestionRunLeaseError) as wrong_owner:
        leases.heartbeat(
            lease_id=claim.lease.id,
            worker_ref="worker-b",
            ttl_seconds=30,
            now=base + timedelta(seconds=2),
        )
    assert wrong_owner.value.code == "INGESTION_RUN_LEASE_NOT_ACTIVE"

    heartbeat = leases.heartbeat(
        lease_id=claim.lease.id,
        worker_ref="worker-a",
        ttl_seconds=30,
        now=base + timedelta(seconds=3),
    )
    assert heartbeat.heartbeat_at == base + timedelta(seconds=3)
    assert heartbeat.expires_at == base + timedelta(seconds=33)
    assert leases.assert_active(
        lease_id=claim.lease.id,
        worker_ref="worker-a",
        now=base + timedelta(seconds=20),
    ) == heartbeat


def test_memory_expiry_requeues_and_reclaim_uses_new_lease() -> None:
    ingestion, repository, leases = _services()
    base = datetime(2026, 8, 2, 7, 0, tzinfo=UTC)
    run = _run(ingestion, index=1, updated_at=base)
    first = leases.claim_next(
        worker_ref="worker-a",
        ttl_seconds=5,
        now=base + timedelta(seconds=1),
    )
    assert first is not None

    recovered = leases.recover_expired(now=base + timedelta(seconds=7))
    assert len(recovered) == 1
    assert recovered[0].state is IngestionRunLeaseState.EXPIRED
    assert ingestion.get_run(run.id).state is IngestionRunState.QUEUED

    with pytest.raises(IngestionRunLeaseError):
        leases.assert_active(
            lease_id=first.lease.id,
            worker_ref="worker-a",
            now=base + timedelta(seconds=7),
        )

    second = leases.claim_next(
        worker_ref="worker-b",
        ttl_seconds=30,
        now=base + timedelta(seconds=8),
    )
    assert second is not None
    assert second.run.id == run.id
    assert second.lease.id != first.lease.id
    assert repository.get_lease(first.lease.id).state is IngestionRunLeaseState.EXPIRED
    assert repository.get_lease(second.lease.id).state is IngestionRunLeaseState.ACTIVE


def test_memory_release_disposition_enforces_run_state() -> None:
    ingestion, _, leases = _services()
    base = datetime(2026, 8, 2, 8, 0, tzinfo=UTC)
    run = _run(ingestion, index=1, updated_at=base)
    claim = leases.claim_next(
        worker_ref="worker-a",
        ttl_seconds=60,
        now=base + timedelta(seconds=1),
    )
    assert claim is not None

    with pytest.raises(IngestionRunLeaseError) as invalid_terminal:
        leases.release(
            lease_id=claim.lease.id,
            worker_ref="worker-a",
            disposition=IngestionRunLeaseReleaseDisposition.TERMINAL,
            now=base + timedelta(seconds=2),
        )
    assert invalid_terminal.value.code == "INGESTION_RUN_LEASE_RELEASE_INVALID"

    released = leases.release(
        lease_id=claim.lease.id,
        worker_ref="worker-a",
        disposition=IngestionRunLeaseReleaseDisposition.REQUEUE,
        now=base + timedelta(seconds=3),
    )
    assert released.state is IngestionRunLeaseState.RELEASED
    assert ingestion.get_run(run.id).state is IngestionRunState.QUEUED

    second = leases.claim_next(
        worker_ref="worker-b",
        ttl_seconds=60,
        now=base + timedelta(seconds=4),
    )
    assert second is not None
    running = ingestion.get_run(run.id)
    ingestion.update_run(
        running.transition(
            IngestionRunState.SUCCEEDED,
            at=base + timedelta(seconds=5),
        )
    )
    terminal_release = leases.release(
        lease_id=second.lease.id,
        worker_ref="worker-b",
        disposition=IngestionRunLeaseReleaseDisposition.TERMINAL,
        now=base + timedelta(seconds=6),
    )
    assert terminal_release.release_disposition is (
        IngestionRunLeaseReleaseDisposition.TERMINAL
    )
    assert ingestion.get_run(run.id).state is IngestionRunState.SUCCEEDED


def test_lease_ttl_and_recovery_limits_are_bounded() -> None:
    _, _, leases = _services()
    with pytest.raises(ValueError, match="TTL"):
        leases.claim_next(worker_ref="worker", ttl_seconds=4)
    with pytest.raises(ValueError, match="TTL"):
        leases.claim_next(worker_ref="worker", ttl_seconds=901)
    with pytest.raises(ValueError, match="recovery limit"):
        leases.recover_expired(limit=1001)
