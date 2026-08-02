from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine

from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.infrastructure.postgres_knowledge import PostgresKnowledgeRepository
from kefe_api.modules.ingestion_orchestration.models import IngestionRunState
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    InMemorySourceAcquisitionObserver,
    InMemorySourceCaptureRegistry,
    SourceAcquisitionCommand,
    SourceAcquisitionOutcome,
    SourceAcquisitionService,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


class SequenceCaptureAdapter:
    def __init__(self, *, adapter_code: str, captures: list[CapturedSource]) -> None:
        self._adapter_code = adapter_code
        self._captures = captures
        self._index = 0

    @property
    def adapter_code(self) -> str:
        return self._adapter_code

    def capture(self, *, external_locator: str, trace_id: str) -> CapturedSource:
        del external_locator, trace_id
        index = min(self._index, len(self._captures) - 1)
        self._index += 1
        return self._captures[index]


def _runtime(*, engine, adapter: SequenceCaptureAdapter):
    knowledge = PostgresKnowledgeRepository(engine)
    ingestion = PostgresIngestionOrchestrationRepository(engine)
    observer = InMemorySourceAcquisitionObserver()
    service = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=IngestionOrchestrationService(ingestion),
        registry=InMemorySourceCaptureRegistry((adapter,)),
        observer=observer,
        clock=lambda: datetime.now(UTC),
    )
    return knowledge, ingestion, observer, service


def _command(*, adapter_code: str, external_locator: str) -> SourceAcquisitionCommand:
    return SourceAcquisitionCommand(
        adapter_code=adapter_code,
        external_locator=external_locator,
        pipeline_code="SOURCE_TO_PROPOSAL",
        pipeline_version="1.0.0",
        configuration_hash="sha256:postgres-source-acquisition-config",
        taxonomy_version="taxonomy-v1",
        methodology_version="methodology-v1",
        locale="en",
        jurisdiction_code="ZZ",
    )


def test_postgres_unchanged_capture_reuses_artifact_and_run_identity() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    suffix = uuid4().hex[:10]
    adapter_code = f"test.pg_replay_{suffix}.v1"
    locator = f"https://example.test/postgres/replay/{suffix}"
    adapter = SequenceCaptureAdapter(
        adapter_code=adapter_code,
        captures=[
            CapturedSource(
                content_hash=f"sha256:postgres-replay:{suffix}",
                raw_storage_ref=f"object://postgres/replay/{suffix}",
            )
        ],
    )
    knowledge, ingestion, observer, service = _runtime(
        engine=engine,
        adapter=adapter,
    )
    command = _command(adapter_code=adapter_code, external_locator=locator)

    first = service.acquire(command, trace_id="postgres-replay-first")
    replay = service.acquire(command, trace_id="postgres-replay-second")

    assert first.outcome is SourceAcquisitionOutcome.ADMITTED
    assert replay.outcome is SourceAcquisitionOutcome.ADMITTED
    assert replay.source_artifact_id == first.source_artifact_id
    assert replay.ingestion_run_id == first.ingestion_run_id
    assert first.source_artifact_id is not None
    artifact = knowledge.get_source_artifact(first.source_artifact_id)
    assert artifact is not None
    assert artifact.adapter_code == adapter_code
    assert artifact.external_locator == locator
    assert first.ingestion_run_id is not None
    assert ingestion.get_run(first.ingestion_run_id).state is IngestionRunState.QUEUED
    assert len(observer.results) == 2


def test_postgres_changed_hash_creates_new_immutable_artifact_and_run() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    suffix = uuid4().hex[:10]
    adapter_code = f"test.pg_changed_{suffix}.v1"
    locator = f"https://example.test/postgres/changed/{suffix}"
    first_hash = f"sha256:postgres-first:{suffix}"
    second_hash = f"sha256:postgres-second:{suffix}"
    adapter = SequenceCaptureAdapter(
        adapter_code=adapter_code,
        captures=[
            CapturedSource(content_hash=first_hash),
            CapturedSource(content_hash=second_hash),
        ],
    )
    knowledge, ingestion, _, service = _runtime(engine=engine, adapter=adapter)
    command = _command(adapter_code=adapter_code, external_locator=locator)

    first = service.acquire(command)
    second = service.acquire(command)

    assert first.outcome is SourceAcquisitionOutcome.ADMITTED
    assert second.outcome is SourceAcquisitionOutcome.ADMITTED
    assert first.source_artifact_id != second.source_artifact_id
    assert first.ingestion_run_id != second.ingestion_run_id
    first_artifact = knowledge.find_source_artifact(
        adapter_code=adapter_code,
        external_locator=locator,
        content_hash=first_hash,
    )
    second_artifact = knowledge.find_source_artifact(
        adapter_code=adapter_code,
        external_locator=locator,
        content_hash=second_hash,
    )
    assert first_artifact is not None and first_artifact.id == first.source_artifact_id
    assert second_artifact is not None and second_artifact.id == second.source_artifact_id
    assert ingestion.get_run(first.ingestion_run_id).state is IngestionRunState.QUEUED
    assert ingestion.get_run(second.ingestion_run_id).state is IngestionRunState.QUEUED


def test_postgres_preexisting_artifact_without_run_is_completed_by_replay() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    suffix = uuid4().hex[:10]
    adapter_code = f"test.pg_recovery_{suffix}.v1"
    locator = f"https://example.test/postgres/recovery/{suffix}"
    content_hash = f"sha256:postgres-recovery:{suffix}"
    adapter = SequenceCaptureAdapter(
        adapter_code=adapter_code,
        captures=[CapturedSource(content_hash=content_hash)],
    )
    knowledge, ingestion, _, service = _runtime(engine=engine, adapter=adapter)
    command = _command(adapter_code=adapter_code, external_locator=locator)
    existing = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code=adapter_code,
            external_locator=locator,
            content_hash=content_hash,
        )
    )

    result = service.acquire(command, trace_id="postgres-recovery")

    assert result.outcome is SourceAcquisitionOutcome.ADMITTED
    assert result.source_artifact_id == existing.id
    assert result.ingestion_run_id is not None
    admitted_run = ingestion.get_run(result.ingestion_run_id)
    assert admitted_run is not None
    assert admitted_run.input_artifact_id == existing.id
    assert admitted_run.state is IngestionRunState.QUEUED
