from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.provider_control import (
    ProviderAdmissionOutcome,
    ProviderCapabilityLifecycle,
    ProviderCapturePermitState,
    ProviderCircuitState,
)
from kefe_api.modules.knowledge.provider_control_memory import (
    InMemorySourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    InMemorySourceAcquisitionObserver,
    InMemorySourceCaptureRegistry,
    RetryableSourceCaptureError,
    SourceAcquisitionCommand,
    SourceAcquisitionOutcome,
    SourceAcquisitionService,
    SourceCaptureAdmissionDecision,
)


class MutableClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


class CaptureAdapter:
    def __init__(
        self,
        *,
        adapter_code: str = "test.provider.v1",
        content_hash: str = "sha256:provider",
        failure_code: str | None = None,
    ) -> None:
        self._adapter_code = adapter_code
        self.content_hash = content_hash
        self.failure_code = failure_code
        self.calls = 0

    @property
    def adapter_code(self) -> str:
        return self._adapter_code

    def capture(self, *, external_locator: str, trace_id: str) -> CapturedSource:
        del external_locator, trace_id
        self.calls += 1
        if self.failure_code is not None:
            raise RetryableSourceCaptureError(self.failure_code)
        return CapturedSource(
            content_hash=self.content_hash,
            raw_storage_ref="secret://must-not-leak",
        )


class CompletionFailingAdmission:
    def admit_capture(self, *, adapter_code: str, at: datetime):
        del adapter_code, at
        from uuid import uuid4

        return SourceCaptureAdmissionDecision(
            allowed=True,
            retryable=False,
            permit_id=uuid4(),
            reason_code="SOURCE_PROVIDER_ADMITTED",
        )

    def complete_capture_success(self, **kwargs):
        del kwargs
        raise RuntimeError("provider control unavailable")

    def complete_capture_failure(self, **kwargs):
        del kwargs
        raise RuntimeError("provider control unavailable")


def _service(
    *,
    base: datetime,
    quota_limit: int = 10,
    failure_threshold: int = 2,
    quota_window_seconds: int = 60,
    circuit_open_seconds: int = 30,
    permit_ttl_seconds: int = 10,
):
    clock = MutableClock(base)
    repository = InMemorySourceProviderAdmissionRepository()
    service = SourceProviderAdmissionService(repository, clock=clock)
    service.register(
        adapter_code="test.provider.v1",
        secret_ref="vault://kefe/providers/test",
        quota_limit=quota_limit,
        quota_window_seconds=quota_window_seconds,
        failure_threshold=failure_threshold,
        circuit_open_seconds=circuit_open_seconds,
        permit_ttl_seconds=permit_ttl_seconds,
        created_at=base,
    )
    return clock, repository, service


def test_secret_reference_and_lifecycle_are_explicit_and_immutable() -> None:
    base = datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    clock, repository, service = _service(base=base)

    with pytest.raises(ValueError, match="opaque reference"):
        service.register(
            adapter_code="test.invalid.v1",
            secret_ref="actual-password-value",
            quota_limit=1,
            quota_window_seconds=60,
            failure_threshold=1,
            circuit_open_seconds=30,
            permit_ttl_seconds=10,
            created_at=base,
        )
    with pytest.raises(ValueError, match="immutable"):
        service.register(
            adapter_code="test.provider.v1",
            secret_ref="vault://kefe/providers/changed",
            quota_limit=10,
            quota_window_seconds=60,
            failure_threshold=2,
            circuit_open_seconds=30,
            permit_ttl_seconds=10,
            created_at=base,
        )

    paused = service.pause("test.provider.v1", at=base + timedelta(seconds=1))
    assert paused.lifecycle_state is ProviderCapabilityLifecycle.PAUSED
    assert service.admit(
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=2),
    ).outcome is ProviderAdmissionOutcome.PAUSED
    resumed = service.resume("test.provider.v1", at=base + timedelta(seconds=3))
    assert resumed.lifecycle_state is ProviderCapabilityLifecycle.ENABLED
    retired = service.retire("test.provider.v1", at=base + timedelta(seconds=4))
    assert retired.lifecycle_state is ProviderCapabilityLifecycle.RETIRED
    with pytest.raises(ValueError):
        service.resume("test.provider.v1", at=base + timedelta(seconds=5))
    assert "vault://" not in repr(
        repository.admit(
            adapter_code="test.provider.v1",
            at=base + timedelta(seconds=6),
        ).as_operational_dict()
    )


def test_fixed_window_quota_returns_exact_retry_after_and_rolls() -> None:
    base = datetime(2026, 8, 2, 13, 0, tzinfo=UTC)
    _, _, service = _service(base=base, quota_limit=1, quota_window_seconds=60)

    admitted = service.admit(adapter_code="test.provider.v1", at=base)
    assert admitted.outcome is ProviderAdmissionOutcome.ADMITTED
    limited = service.admit(
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=10),
    )
    assert limited.outcome is ProviderAdmissionOutcome.RATE_LIMITED
    assert limited.retry_after_seconds == 50

    rolled = service.admit(
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=60),
    )
    assert rolled.outcome is ProviderAdmissionOutcome.ADMITTED


def test_failure_threshold_half_open_probe_and_success_close_circuit() -> None:
    base = datetime(2026, 8, 2, 14, 0, tzinfo=UTC)
    _, repository, service = _service(
        base=base,
        failure_threshold=2,
        circuit_open_seconds=30,
    )

    first = service.admit(adapter_code="test.provider.v1", at=base)
    service.complete_failure(
        permit_id=first.permit_id,
        adapter_code="test.provider.v1",
        failure_code="FIRST_FAILURE",
        at=base + timedelta(seconds=1),
    )
    second = service.admit(
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=2),
    )
    service.complete_failure(
        permit_id=second.permit_id,
        adapter_code="test.provider.v1",
        failure_code="SECOND_FAILURE",
        at=base + timedelta(seconds=3),
    )
    opened = service.admit(
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=4),
    )
    assert opened.outcome is ProviderAdmissionOutcome.CIRCUIT_OPEN
    assert opened.retry_after_seconds == 29

    probe = service.admit(
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=33),
    )
    assert probe.outcome is ProviderAdmissionOutcome.ADMITTED
    assert probe.circuit_state is ProviderCircuitState.HALF_OPEN
    blocked_probe = service.admit(
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=34),
    )
    assert blocked_probe.outcome is ProviderAdmissionOutcome.CIRCUIT_OPEN
    assert blocked_probe.reason_code == "SOURCE_PROVIDER_HALF_OPEN_PROBE_ACTIVE"

    service.complete_success(
        permit_id=probe.permit_id,
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=35),
    )
    capability = repository.get("test.provider.v1")
    assert capability.circuit_state is ProviderCircuitState.CLOSED
    assert capability.consecutive_failure_count == 0


def test_half_open_probe_failure_reopens_and_expired_permit_is_abandoned() -> None:
    base = datetime(2026, 8, 2, 15, 0, tzinfo=UTC)
    _, repository, service = _service(
        base=base,
        failure_threshold=1,
        circuit_open_seconds=5,
        permit_ttl_seconds=5,
    )
    first = service.admit(adapter_code="test.provider.v1", at=base)
    service.complete_failure(
        permit_id=first.permit_id,
        adapter_code="test.provider.v1",
        failure_code="OPEN",
        at=base + timedelta(seconds=1),
    )
    probe = service.admit(
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=6),
    )
    service.complete_failure(
        permit_id=probe.permit_id,
        adapter_code="test.provider.v1",
        failure_code="PROBE_FAILED",
        at=base + timedelta(seconds=7),
    )
    assert service.admit(
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=8),
    ).outcome is ProviderAdmissionOutcome.CIRCUIT_OPEN

    other_clock, other_repository, other_service = _service(
        base=base,
        failure_threshold=1,
        permit_ttl_seconds=5,
    )
    del other_clock
    stale = other_service.admit(adapter_code="test.provider.v1", at=base)
    denied = other_service.admit(
        adapter_code="test.provider.v1",
        at=base + timedelta(seconds=5),
    )
    assert denied.outcome is ProviderAdmissionOutcome.CIRCUIT_OPEN
    assert other_repository._permits[stale.permit_id].state is (
        ProviderCapturePermitState.ABANDONED
    )


def test_source_acquisition_requires_capability_and_closes_permit_before_write() -> None:
    base = datetime(2026, 8, 2, 16, 0, tzinfo=UTC)
    clock = MutableClock(base)
    adapter = CaptureAdapter()
    knowledge = InMemoryKnowledgeRepository()
    ingestion = InMemoryIngestionOrchestrationRepository()
    provider_repository = InMemorySourceProviderAdmissionRepository()
    provider = SourceProviderAdmissionService(provider_repository, clock=clock)
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=IngestionOrchestrationService(ingestion),
        registry=InMemorySourceCaptureRegistry((adapter,)),
        observer=InMemorySourceAcquisitionObserver(),
        admission=provider,
        clock=clock,
    )
    command = SourceAcquisitionCommand(
        adapter_code=adapter.adapter_code,
        external_locator="https://private.example/provider-source",
        pipeline_code="PROVIDER_PIPELINE",
        pipeline_version="1.0.0",
        configuration_hash="sha256:provider-config",
    )

    blocked = acquisition.acquire(command)
    assert blocked.outcome is SourceAcquisitionOutcome.BLOCKED
    assert blocked.error_code == "SOURCE_PROVIDER_NOT_REGISTERED"
    assert adapter.calls == 0
    assert knowledge._source_artifacts == {}

    provider.register(
        adapter_code=adapter.adapter_code,
        secret_ref="secret://providers/test",
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=2,
        circuit_open_seconds=30,
        permit_ttl_seconds=10,
        created_at=base,
    )
    admitted = acquisition.acquire(command)
    assert admitted.outcome is SourceAcquisitionOutcome.ADMITTED
    assert adapter.calls == 1
    permits = tuple(provider_repository._permits.values())
    assert len(permits) == 1
    assert permits[0].state is ProviderCapturePermitState.SUCCEEDED
    assert knowledge.get_source_artifact(admitted.source_artifact_id) is not None


def test_capture_failure_updates_circuit_and_completion_failure_writes_nothing() -> None:
    base = datetime(2026, 8, 2, 17, 0, tzinfo=UTC)
    clock = MutableClock(base)
    failing_adapter = CaptureAdapter(failure_code="PROVIDER_TEMPORARY")
    knowledge = InMemoryKnowledgeRepository()
    ingestion = InMemoryIngestionOrchestrationRepository()
    repository = InMemorySourceProviderAdmissionRepository()
    provider = SourceProviderAdmissionService(repository, clock=clock)
    provider.register(
        adapter_code=failing_adapter.adapter_code,
        secret_ref="kms://providers/test",
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=1,
        circuit_open_seconds=30,
        permit_ttl_seconds=10,
        created_at=base,
    )
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=IngestionOrchestrationService(ingestion),
        registry=InMemorySourceCaptureRegistry((failing_adapter,)),
        observer=InMemorySourceAcquisitionObserver(),
        admission=provider,
        clock=clock,
    )
    command = SourceAcquisitionCommand(
        adapter_code=failing_adapter.adapter_code,
        external_locator="https://private.example/provider-failure",
        pipeline_code="PROVIDER_PIPELINE",
        pipeline_version="1.0.0",
        configuration_hash="sha256:provider-config",
    )

    failed = acquisition.acquire(command)
    assert failed.outcome is SourceAcquisitionOutcome.RETRYABLE_FAILURE
    assert repository.get("test.provider.v1").circuit_state is (
        ProviderCircuitState.OPEN
    )
    assert knowledge._source_artifacts == {}

    successful_adapter = CaptureAdapter(adapter_code="test.completion.v1")
    fail_closed_knowledge = InMemoryKnowledgeRepository()
    fail_closed = SourceAcquisitionService(
        knowledge_repository=fail_closed_knowledge,
        ingestion_service=IngestionOrchestrationService(
            InMemoryIngestionOrchestrationRepository()
        ),
        registry=InMemorySourceCaptureRegistry((successful_adapter,)),
        observer=InMemorySourceAcquisitionObserver(),
        admission=CompletionFailingAdmission(),
        clock=clock,
    )
    completion_failed = fail_closed.acquire(
        SourceAcquisitionCommand(
            adapter_code=successful_adapter.adapter_code,
            external_locator="https://private.example/completion",
            pipeline_code="PROVIDER_PIPELINE",
            pipeline_version="1.0.0",
            configuration_hash="sha256:provider-config",
        )
    )
    assert completion_failed.outcome is SourceAcquisitionOutcome.RETRYABLE_FAILURE
    assert completion_failed.error_code == "SOURCE_PROVIDER_PERMIT_COMPLETION_FAILED"
    assert fail_closed_knowledge._source_artifacts == {}
