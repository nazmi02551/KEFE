from __future__ import annotations

import pickle
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.provider_control_memory import (
    InMemorySourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.provider_execution_context import (
    ProviderPermitContextError,
    ProviderPermitExecutionContext,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    InMemoryCredentialAwareSourceCaptureRegistry,
    InMemorySecretResolverRegistry,
    SecretLease,
    SecretResolutionRetryableError,
    SecureProviderCaptureExecutor,
)
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    FinalSourceCaptureError,
    InMemorySourceCaptureRegistry,
    NoOpSourceAcquisitionObserver,
    RetryableSourceCaptureError,
    SourceAcquisitionCommand,
    SourceAcquisitionOutcome,
    SourceAcquisitionService,
)

NOW = datetime(2026, 8, 2, 16, 0, tzinfo=UTC)
ADAPTER_CODE = "test.secure_provider.v1"
SECRET_REF = "secret://providers/test-secure"
SECRET_VALUE = b"never-persist-this-secret"


class StaticExecutionContexts:
    def __init__(self, context: ProviderPermitExecutionContext) -> None:
        self.context = context

    def get_active_execution_context(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
    ) -> ProviderPermitExecutionContext:
        if (
            permit_id != self.context.permit_id
            or adapter_code != self.context.adapter_code
            or at >= self.context.permit_expires_at
        ):
            raise ProviderPermitContextError()
        return self.context


class StaticSecretResolver:
    scheme = "secret"

    def __init__(self, material: bytes = SECRET_VALUE) -> None:
        self.material = material
        self.last_lease: SecretLease | None = None

    def resolve(
        self,
        *,
        secret_ref: str,
        adapter_code: str,
        permit_id: UUID,
        at: datetime,
        expires_at: datetime,
    ) -> SecretLease:
        assert secret_ref == SECRET_REF
        assert adapter_code == ADAPTER_CODE
        assert permit_id
        assert at < expires_at
        self.last_lease = SecretLease(self.material, expires_at=expires_at)
        return self.last_lease


class RetryableSecretResolver(StaticSecretResolver):
    def resolve(self, **kwargs):
        del kwargs
        raise SecretResolutionRetryableError()


class CredentialAwareAdapter:
    adapter_code = ADAPTER_CODE

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.observed = False

    def capture(
        self,
        *,
        external_locator: str,
        trace_id: str,
        secret,
        at: datetime,
    ) -> CapturedSource:
        assert external_locator == "source://fixture"
        assert trace_id
        assert at == NOW

        def use(material: memoryview) -> None:
            assert material.tobytes() == SECRET_VALUE
            self.observed = True
            if self.fail:
                raise RuntimeError("adapter failed without secret text")

        secret.use_bytes(use, at=at)
        return CapturedSource(
            content_hash="sha256:secure-capture",
            raw_storage_ref="opaque://captured/source",
        )


def _context(permit_id: UUID) -> ProviderPermitExecutionContext:
    return ProviderPermitExecutionContext(
        permit_id=permit_id,
        adapter_code=ADAPTER_CODE,
        secret_ref=SECRET_REF,
        permit_expires_at=NOW + timedelta(minutes=1),
    )


def test_secret_lease_redacts_forbids_serialization_and_zeroizes() -> None:
    lease = SecretLease(SECRET_VALUE, expires_at=NOW + timedelta(minutes=1))
    assert "never-persist" not in repr(lease)
    assert "REDACTED" in repr(lease)
    assert lease.use_bytes(lambda value: value.tobytes(), at=NOW) == SECRET_VALUE
    with pytest.raises(TypeError):
        _ = lease == lease
    with pytest.raises(TypeError):
        pickle.dumps(lease)

    material = lease._material
    lease.close()
    assert lease.closed
    assert bytes(material) == bytes(len(SECRET_VALUE))
    with pytest.raises(RuntimeError, match="SECRET_LEASE_CLOSED"):
        lease.use_bytes(lambda value: value.tobytes(), at=NOW)


def test_secret_lease_rejects_expiry_and_context_repr_redacts_reference() -> None:
    lease = SecretLease(SECRET_VALUE, expires_at=NOW)
    with pytest.raises(RuntimeError, match="SECRET_LEASE_EXPIRED"):
        lease.use_bytes(lambda value: value.tobytes(), at=NOW)
    context = _context(UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))
    assert SECRET_REF not in repr(context)
    assert "REDACTED" in repr(context)


def test_secure_executor_uses_exact_registries_and_zeroizes_after_success() -> None:
    permit_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    resolver = StaticSecretResolver()
    adapter = CredentialAwareAdapter()
    executor = SecureProviderCaptureExecutor(
        contexts=StaticExecutionContexts(_context(permit_id)),
        resolvers=InMemorySecretResolverRegistry((resolver,)),
        adapters=InMemoryCredentialAwareSourceCaptureRegistry((adapter,)),
    )

    captured = executor.capture(
        adapter_code=ADAPTER_CODE,
        permit_id=permit_id,
        external_locator="source://fixture",
        trace_id="trace-secure",
        at=NOW,
    )

    assert captured.content_hash == "sha256:secure-capture"
    assert adapter.observed
    assert resolver.last_lease is not None
    assert resolver.last_lease.closed
    assert bytes(resolver.last_lease._material) == bytes(len(SECRET_VALUE))


def test_secure_executor_zeroizes_after_adapter_or_resolution_failure() -> None:
    permit_id = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
    resolver = StaticSecretResolver()
    executor = SecureProviderCaptureExecutor(
        contexts=StaticExecutionContexts(_context(permit_id)),
        resolvers=InMemorySecretResolverRegistry((resolver,)),
        adapters=InMemoryCredentialAwareSourceCaptureRegistry(
            (CredentialAwareAdapter(fail=True),)
        ),
    )
    with pytest.raises(RuntimeError, match="adapter failed"):
        executor.capture(
            adapter_code=ADAPTER_CODE,
            permit_id=permit_id,
            external_locator="source://fixture",
            trace_id="trace-failure",
            at=NOW,
        )
    assert resolver.last_lease is not None and resolver.last_lease.closed
    assert bytes(resolver.last_lease._material) == bytes(len(SECRET_VALUE))

    retryable = SecureProviderCaptureExecutor(
        contexts=StaticExecutionContexts(_context(permit_id)),
        resolvers=InMemorySecretResolverRegistry((RetryableSecretResolver(),)),
        adapters=InMemoryCredentialAwareSourceCaptureRegistry(
            (CredentialAwareAdapter(),)
        ),
    )
    with pytest.raises(RetryableSourceCaptureError) as captured_error:
        retryable.capture(
            adapter_code=ADAPTER_CODE,
            permit_id=permit_id,
            external_locator="source://fixture",
            trace_id="trace-resolution",
            at=NOW,
        )
    assert captured_error.value.code == "SOURCE_SECRET_RESOLUTION_RETRYABLE"
    assert SECRET_REF not in str(captured_error.value)
    assert SECRET_VALUE.decode() not in str(captured_error.value)


def _build_secure_acquisition(*, include_resolver: bool = True):
    knowledge = InMemoryKnowledgeRepository()
    ingestion_repository = InMemoryIngestionOrchestrationRepository()
    ingestion = IngestionOrchestrationService(ingestion_repository)
    provider_repository = InMemorySourceProviderAdmissionRepository()
    provider = SourceProviderAdmissionService(provider_repository, clock=lambda: NOW)
    provider.register(
        adapter_code=ADAPTER_CODE,
        secret_ref=SECRET_REF,
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=60,
        permit_ttl_seconds=30,
        created_at=NOW,
    )
    resolver = StaticSecretResolver()
    executor = SecureProviderCaptureExecutor(
        contexts=provider_repository,
        resolvers=InMemorySecretResolverRegistry(
            (resolver,) if include_resolver else ()
        ),
        adapters=InMemoryCredentialAwareSourceCaptureRegistry(
            (CredentialAwareAdapter(),)
        ),
    )
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=ingestion,
        registry=InMemorySourceCaptureRegistry(),
        observer=NoOpSourceAcquisitionObserver(),
        admission=provider,
        capture_executor=executor,
        clock=lambda: NOW,
    )
    command = SourceAcquisitionCommand(
        adapter_code=ADAPTER_CODE,
        external_locator="source://fixture",
        pipeline_code="SECURE_CAPTURE_PIPELINE",
        pipeline_version="1.0.0",
        configuration_hash="sha256:secure-config",
    )
    return acquisition, command, knowledge, ingestion_repository, provider_repository


def test_secure_source_acquisition_completes_permit_before_persistence() -> None:
    acquisition, command, knowledge, ingestion, providers = _build_secure_acquisition()
    result = acquisition.acquire(command, trace_id="trace-acquisition")

    assert result.outcome is SourceAcquisitionOutcome.ADMITTED
    assert len(knowledge._source_artifacts) == 1
    assert len(ingestion._runs) == 1
    permit = next(iter(providers._permits.values()))
    assert permit.state.value == "SUCCEEDED"
    assert SECRET_REF not in repr(result.as_operational_dict())
    assert SECRET_VALUE.decode() not in repr(result.as_operational_dict())


def test_resolution_failure_closes_permit_and_writes_nothing() -> None:
    acquisition, command, knowledge, ingestion, providers = _build_secure_acquisition(
        include_resolver=False
    )
    result = acquisition.acquire(command, trace_id="trace-no-resolver")

    assert result.outcome is SourceAcquisitionOutcome.FINAL_FAILURE
    assert result.error_code == "SOURCE_SECRET_RESOLVER_NOT_REGISTERED"
    assert len(knowledge._source_artifacts) == 0
    assert len(ingestion._runs) == 0
    permit = next(iter(providers._permits.values()))
    assert permit.state.value == "FAILED"
    assert permit.failure_code == "SOURCE_SECRET_RESOLVER_NOT_REGISTERED"
    assert SECRET_REF not in repr(result.as_operational_dict())


def test_empty_production_style_registries_fail_closed() -> None:
    permit_id = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
    executor = SecureProviderCaptureExecutor(
        contexts=StaticExecutionContexts(_context(permit_id)),
        resolvers=InMemorySecretResolverRegistry(),
        adapters=InMemoryCredentialAwareSourceCaptureRegistry(),
    )
    with pytest.raises(FinalSourceCaptureError) as error:
        executor.capture(
            adapter_code=ADAPTER_CODE,
            permit_id=permit_id,
            external_locator="source://fixture",
            trace_id="trace-empty",
            at=NOW,
        )
    assert error.value.code == "SOURCE_SECRET_RESOLVER_NOT_REGISTERED"
