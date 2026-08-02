from __future__ import annotations

from collections import deque
from datetime import UTC, datetime

import pytest

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.models import IngestionRunState
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.models import SourceArtifact
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    FinalSourceCaptureError,
    InMemorySourceAcquisitionObserver,
    InMemorySourceCaptureRegistry,
    RetryableSourceCaptureError,
    SourceAcquisitionCommand,
    SourceAcquisitionOutcome,
    SourceAcquisitionService,
    require_versioned_adapter_code,
)


class SequenceCaptureAdapter:
    def __init__(
        self,
        *captures: CapturedSource,
        adapter_code: str = "test.capture.v1",
    ) -> None:
        self._adapter_code = adapter_code
        self._captures = deque(captures)
        self.calls: list[tuple[str, str]] = []
        self._last = captures[-1] if captures else None

    @property
    def adapter_code(self) -> str:
        return self._adapter_code

    def capture(self, *, external_locator: str, trace_id: str) -> CapturedSource:
        self.calls.append((external_locator, trace_id))
        if self._captures:
            self._last = self._captures.popleft()
        assert self._last is not None
        return self._last


class RetryableAdapter:
    adapter_code = "test.retryable.v1"

    def capture(self, *, external_locator: str, trace_id: str) -> CapturedSource:
        del external_locator, trace_id
        raise RetryableSourceCaptureError("SOURCE_TEMPORARILY_UNAVAILABLE")


class FinalAdapter:
    adapter_code = "test.final.v1"

    def capture(self, *, external_locator: str, trace_id: str) -> CapturedSource:
        del external_locator, trace_id
        raise FinalSourceCaptureError("SOURCE_LOCATOR_INVALID")


class UnexpectedAdapter:
    adapter_code = "test.unexpected.v1"

    def capture(self, *, external_locator: str, trace_id: str) -> CapturedSource:
        del external_locator, trace_id
        raise RuntimeError("secret provider exception text")


class ExplodingObserver:
    def record(self, result) -> None:
        del result
        raise RuntimeError("observer unavailable")


def _command(
    *,
    adapter_code: str = "test.capture.v1",
    external_locator: str = "https://example.test/source/1",
) -> SourceAcquisitionCommand:
    return SourceAcquisitionCommand(
        adapter_code=adapter_code,
        external_locator=external_locator,
        pipeline_code="SOURCE_TO_PROPOSAL",
        pipeline_version="1.0.0",
        configuration_hash="sha256:source-acquisition-config",
        taxonomy_version="taxonomy-v1",
        methodology_version="methodology-v1",
        locale="en",
        jurisdiction_code="ZZ",
    )


def _runtime(*adapters, observer=None):
    knowledge = InMemoryKnowledgeRepository()
    ingestion = InMemoryIngestionOrchestrationRepository()
    acquisition_observer = observer or InMemorySourceAcquisitionObserver()
    service = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=IngestionOrchestrationService(ingestion),
        registry=InMemorySourceCaptureRegistry(tuple(adapters)),
        observer=acquisition_observer,
        clock=lambda: datetime(2026, 8, 2, 10, 0, tzinfo=UTC),
    )
    return knowledge, ingestion, acquisition_observer, service


def test_versioned_adapter_validation_and_duplicate_rejection() -> None:
    require_versioned_adapter_code("public.rss.v1")
    with pytest.raises(ValueError):
        require_versioned_adapter_code("public.rss")
    with pytest.raises(ValueError):
        require_versioned_adapter_code("Public.RSS.v1")

    first = SequenceCaptureAdapter(CapturedSource(content_hash="sha256:a"))
    second = SequenceCaptureAdapter(CapturedSource(content_hash="sha256:b"))
    with pytest.raises(ValueError, match="duplicate"):
        InMemorySourceCaptureRegistry((first, second))


def test_unchanged_capture_replays_same_artifact_and_run_without_payload_leak() -> None:
    capture = CapturedSource(
        content_hash="sha256:unchanged",
        external_id="external-1",
        canonical_url="https://example.test/canonical/1",
        publisher_or_issuer="Example Publisher",
        language_code="en",
        jurisdiction_code="ZZ",
        raw_storage_ref="object://source/unchanged",
    )
    adapter = SequenceCaptureAdapter(capture)
    knowledge, ingestion, observer, service = _runtime(adapter)
    command = _command()

    first = service.acquire(command, trace_id="trace-first")
    replay = service.acquire(command, trace_id="trace-replay")

    assert first.outcome is SourceAcquisitionOutcome.ADMITTED
    assert replay.outcome is SourceAcquisitionOutcome.ADMITTED
    assert replay.source_artifact_id == first.source_artifact_id
    assert replay.ingestion_run_id == first.ingestion_run_id
    assert first.source_artifact_id is not None
    artifact = knowledge.get_source_artifact(first.source_artifact_id)
    assert artifact is not None
    assert artifact.content_hash == capture.content_hash
    assert first.ingestion_run_id is not None
    assert ingestion.get_run(first.ingestion_run_id).state is IngestionRunState.QUEUED
    assert len(observer.results) == 2
    operational = observer.results[0].as_operational_dict()
    assert set(operational) == {
        "outcome",
        "adapter_code",
        "pipeline_code",
        "pipeline_version",
        "trace_id",
        "source_artifact_id",
        "ingestion_run_id",
        "duration_ms",
        "error_code",
    }
    assert "object://source/unchanged" not in repr(operational)


def test_changed_content_hash_creates_new_artifact_and_run() -> None:
    adapter = SequenceCaptureAdapter(
        CapturedSource(content_hash="sha256:first"),
        CapturedSource(content_hash="sha256:second"),
    )
    knowledge, ingestion, _, service = _runtime(adapter)
    command = _command()

    first = service.acquire(command)
    second = service.acquire(command)

    assert first.source_artifact_id != second.source_artifact_id
    assert first.ingestion_run_id != second.ingestion_run_id
    assert knowledge.find_source_artifact(
        adapter_code=command.adapter_code,
        external_locator=command.external_locator,
        content_hash="sha256:first",
    ).id == first.source_artifact_id
    assert knowledge.find_source_artifact(
        adapter_code=command.adapter_code,
        external_locator=command.external_locator,
        content_hash="sha256:second",
    ).id == second.source_artifact_id
    assert ingestion.get_run(first.ingestion_run_id).state is IngestionRunState.QUEUED
    assert ingestion.get_run(second.ingestion_run_id).state is IngestionRunState.QUEUED


def test_preexisting_artifact_without_run_is_completed_by_replay() -> None:
    adapter = SequenceCaptureAdapter(CapturedSource(content_hash="sha256:recovery"))
    knowledge, ingestion, _, service = _runtime(adapter)
    command = _command()
    existing = knowledge.add_source_artifact(
        SourceArtifact.create(
            adapter_code=command.adapter_code,
            external_locator=command.external_locator,
            content_hash="sha256:recovery",
        )
    )
    assert ingestion._runs == {}

    result = service.acquire(command, trace_id="trace-recovery")

    assert result.outcome is SourceAcquisitionOutcome.ADMITTED
    assert result.source_artifact_id == existing.id
    assert result.ingestion_run_id is not None
    assert ingestion.get_run(result.ingestion_run_id).input_artifact_id == existing.id


def test_capture_failures_and_missing_adapter_produce_zero_writes() -> None:
    cases = (
        (
            RetryableAdapter(),
            "test.retryable.v1",
            SourceAcquisitionOutcome.RETRYABLE_FAILURE,
            "SOURCE_TEMPORARILY_UNAVAILABLE",
        ),
        (
            FinalAdapter(),
            "test.final.v1",
            SourceAcquisitionOutcome.FINAL_FAILURE,
            "SOURCE_LOCATOR_INVALID",
        ),
        (
            UnexpectedAdapter(),
            "test.unexpected.v1",
            SourceAcquisitionOutcome.FINAL_FAILURE,
            "UNEXPECTED_SOURCE_CAPTURE_FAILURE",
        ),
    )
    for adapter, code, outcome, error_code in cases:
        knowledge, ingestion, observer, service = _runtime(adapter)
        command = _command(adapter_code=code)
        result = service.acquire(command)
        assert result.outcome is outcome
        assert result.error_code == error_code
        assert result.source_artifact_id is None
        assert result.ingestion_run_id is None
        assert knowledge._source_artifacts == {}
        assert ingestion._runs == {}
        assert "secret provider exception text" not in repr(
            observer.results[0].as_operational_dict()
        )

    knowledge, ingestion, observer, service = _runtime()
    blocked = service.acquire(_command(adapter_code="missing.adapter.v1"))
    assert blocked.outcome is SourceAcquisitionOutcome.BLOCKED
    assert blocked.error_code == "SOURCE_CAPTURE_ADAPTER_NOT_REGISTERED"
    assert knowledge._source_artifacts == {}
    assert ingestion._runs == {}
    assert len(observer.results) == 1


def test_observer_failure_does_not_change_admission_result() -> None:
    adapter = SequenceCaptureAdapter(CapturedSource(content_hash="sha256:observer"))
    knowledge, ingestion, _, service = _runtime(
        adapter,
        observer=ExplodingObserver(),
    )

    result = service.acquire(_command(), trace_id="trace-observer")

    assert result.outcome is SourceAcquisitionOutcome.ADMITTED
    assert result.source_artifact_id is not None
    assert knowledge.get_source_artifact(result.source_artifact_id) is not None
    assert result.ingestion_run_id is not None
    assert ingestion.get_run(result.ingestion_run_id) is not None
