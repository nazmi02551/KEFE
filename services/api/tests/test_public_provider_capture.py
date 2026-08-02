from __future__ import annotations

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
from kefe_api.modules.knowledge.provider_control import (
    ProviderCredentialMode,
    SourceProviderCapability,
)
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
from kefe_api.modules.knowledge.provider_public_execution import (
    CredentialModeRoutingProviderCaptureExecutor,
    InMemoryPublicSourceCaptureRegistry,
    PermitBoundPublicCaptureExecutor,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    InMemoryCredentialAwareSourceCaptureRegistry,
    InMemorySecretResolverRegistry,
    SecureProviderCaptureExecutor,
)
from kefe_api.modules.knowledge.source_acquisition import (
    CapturedSource,
    FinalSourceCaptureError,
    InMemorySourceCaptureRegistry,
    NoOpSourceAcquisitionObserver,
    SourceAcquisitionCommand,
    SourceAcquisitionOutcome,
    SourceAcquisitionService,
)

NOW = datetime(2026, 8, 3, 0, 0, tzinfo=UTC)
PUBLIC_ADAPTER = "test.public_provider.v1"
SECRET_ADAPTER = "test.secret_provider.v1"


class StaticContexts:
    def __init__(self, context: ProviderPermitExecutionContext) -> None:
        self.context = context
        self.calls = 0

    def get_active_execution_context(
        self,
        *,
        permit_id: UUID,
        adapter_code: str,
        at: datetime,
    ) -> ProviderPermitExecutionContext:
        self.calls += 1
        if (
            permit_id != self.context.permit_id
            or adapter_code != self.context.adapter_code
            or at >= self.context.permit_expires_at
        ):
            raise ProviderPermitContextError()
        return self.context


class PublicAdapter:
    adapter_code = PUBLIC_ADAPTER

    def __init__(self, *, result: object | None = None) -> None:
        self.calls = 0
        self.result = result

    def capture(
        self,
        *,
        external_locator: str,
        trace_id: str,
        at: datetime,
    ) -> CapturedSource:
        assert external_locator == "https://public.example/feed"
        assert trace_id
        assert at == NOW
        self.calls += 1
        if self.result is not None:
            return self.result  # type: ignore[return-value]
        return CapturedSource(
            content_hash="sha256:public-capture",
            canonical_url=external_locator,
            raw_storage_ref="evidence://sha256/public-capture",
        )


class ResolverLookupSpy:
    def __init__(self) -> None:
        self.called = False

    def get_for_reference(self, secret_ref: str):
        del secret_ref
        self.called = True
        raise AssertionError("resolver lookup must not occur for PUBLIC mode")


class RecordingExecutor:
    def __init__(self, result: CapturedSource) -> None:
        self.result = result
        self.calls = 0

    def capture(self, **kwargs) -> CapturedSource:
        del kwargs
        self.calls += 1
        return self.result


def _context(
    *,
    permit_id: UUID,
    adapter_code: str = PUBLIC_ADAPTER,
    mode: ProviderCredentialMode = ProviderCredentialMode.PUBLIC,
) -> ProviderPermitExecutionContext:
    return ProviderPermitExecutionContext(
        permit_id=permit_id,
        adapter_code=adapter_code,
        secret_ref=(
            None
            if mode is ProviderCredentialMode.PUBLIC
            else "secret://providers/test"
        ),
        permit_expires_at=NOW + timedelta(minutes=1),
        credential_mode=mode,
    )


def test_provider_capability_credential_mode_cross_fields_are_exact() -> None:
    public = SourceProviderCapability.create(
        adapter_code=PUBLIC_ADAPTER,
        credential_mode=ProviderCredentialMode.PUBLIC,
        secret_ref=None,
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=30,
        permit_ttl_seconds=10,
        created_at=NOW,
    )
    assert public.credential_mode is ProviderCredentialMode.PUBLIC
    assert public.secret_ref is None

    secret = SourceProviderCapability.create(
        adapter_code=SECRET_ADAPTER,
        secret_ref="vault://providers/test",
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=30,
        permit_ttl_seconds=10,
        created_at=NOW,
    )
    assert secret.credential_mode is ProviderCredentialMode.SECRET_REF

    with pytest.raises(ValueError, match="cannot contain secret_ref"):
        SourceProviderCapability.create(
            adapter_code="test.invalid_public.v1",
            credential_mode=ProviderCredentialMode.PUBLIC,
            secret_ref="secret://forbidden",
            quota_limit=1,
            quota_window_seconds=60,
            failure_threshold=1,
            circuit_open_seconds=30,
            permit_ttl_seconds=10,
            created_at=NOW,
        )
    with pytest.raises(ValueError, match="requires secret_ref"):
        SourceProviderCapability.create(
            adapter_code="test.invalid_secret.v1",
            credential_mode=ProviderCredentialMode.SECRET_REF,
            secret_ref=None,
            quota_limit=1,
            quota_window_seconds=60,
            failure_threshold=1,
            circuit_open_seconds=30,
            permit_ttl_seconds=10,
            created_at=NOW,
        )


def test_public_executor_requires_exact_public_context_and_adapter() -> None:
    permit_id = UUID("11111111-1111-1111-1111-111111111111")
    adapter = PublicAdapter()
    contexts = StaticContexts(_context(permit_id=permit_id))
    executor = PermitBoundPublicCaptureExecutor(
        contexts=contexts,
        adapters=InMemoryPublicSourceCaptureRegistry((adapter,)),
    )

    captured = executor.capture(
        adapter_code=PUBLIC_ADAPTER,
        permit_id=permit_id,
        external_locator="https://public.example/feed",
        trace_id="trace-public",
        at=NOW,
    )
    assert captured.content_hash == "sha256:public-capture"
    assert adapter.calls == 1

    missing = PermitBoundPublicCaptureExecutor(
        contexts=contexts,
        adapters=InMemoryPublicSourceCaptureRegistry(),
    )
    with pytest.raises(FinalSourceCaptureError) as error:
        missing.capture(
            adapter_code=PUBLIC_ADAPTER,
            permit_id=permit_id,
            external_locator="https://public.example/feed",
            trace_id="trace-missing",
            at=NOW,
        )
    assert error.value.code == "SOURCE_PUBLIC_ADAPTER_NOT_REGISTERED"


def test_public_and_credentialed_executors_reject_cross_mode_before_side_effects() -> None:
    permit_id = UUID("22222222-2222-2222-2222-222222222222")
    public_adapter = PublicAdapter()
    public_executor = PermitBoundPublicCaptureExecutor(
        contexts=StaticContexts(
            _context(
                permit_id=permit_id,
                adapter_code=SECRET_ADAPTER,
                mode=ProviderCredentialMode.SECRET_REF,
            )
        ),
        adapters=InMemoryPublicSourceCaptureRegistry((public_adapter,)),
    )
    with pytest.raises(FinalSourceCaptureError) as public_error:
        public_executor.capture(
            adapter_code=SECRET_ADAPTER,
            permit_id=permit_id,
            external_locator="https://public.example/feed",
            trace_id="trace-mode",
            at=NOW,
        )
    assert public_error.value.code == "SOURCE_PROVIDER_CREDENTIAL_MODE_MISMATCH"
    assert public_adapter.calls == 0

    resolver_spy = ResolverLookupSpy()
    secure_executor = SecureProviderCaptureExecutor(
        contexts=StaticContexts(_context(permit_id=permit_id)),
        resolvers=resolver_spy,  # type: ignore[arg-type]
        adapters=InMemoryCredentialAwareSourceCaptureRegistry(),
    )
    with pytest.raises(FinalSourceCaptureError) as secure_error:
        secure_executor.capture(
            adapter_code=PUBLIC_ADAPTER,
            permit_id=permit_id,
            external_locator="https://public.example/feed",
            trace_id="trace-no-secret",
            at=NOW,
        )
    assert secure_error.value.code == "SOURCE_PROVIDER_CREDENTIAL_MODE_MISMATCH"
    assert resolver_spy.called is False


def test_public_executor_rejects_invalid_permit_and_non_exact_result() -> None:
    permit_id = UUID("33333333-3333-3333-3333-333333333333")
    contexts = StaticContexts(_context(permit_id=permit_id))
    executor = PermitBoundPublicCaptureExecutor(
        contexts=contexts,
        adapters=InMemoryPublicSourceCaptureRegistry(
            (PublicAdapter(result={"content_hash": "not-a-model"}),)
        ),
    )
    with pytest.raises(FinalSourceCaptureError) as contract_error:
        executor.capture(
            adapter_code=PUBLIC_ADAPTER,
            permit_id=permit_id,
            external_locator="https://public.example/feed",
            trace_id="trace-invalid",
            at=NOW,
        )
    assert contract_error.value.code == "SOURCE_PUBLIC_CAPTURE_CONTRACT_INVALID"

    with pytest.raises(FinalSourceCaptureError) as permit_error:
        executor.capture(
            adapter_code=PUBLIC_ADAPTER,
            permit_id=UUID("44444444-4444-4444-4444-444444444444"),
            external_locator="https://public.example/feed",
            trace_id="trace-wrong-permit",
            at=NOW,
        )
    assert permit_error.value.code == "SOURCE_PROVIDER_PERMIT_CONTEXT_INVALID"


def test_routing_executor_dispatches_only_by_exact_context_mode() -> None:
    public_permit = UUID("55555555-5555-5555-5555-555555555555")
    public_result = CapturedSource(content_hash="sha256:routed-public")
    public = RecordingExecutor(public_result)
    credentialed = RecordingExecutor(CapturedSource(content_hash="sha256:credentialed"))
    router = CredentialModeRoutingProviderCaptureExecutor(
        contexts=StaticContexts(_context(permit_id=public_permit)),
        public_executor=public,  # type: ignore[arg-type]
        credentialed_executor=credentialed,  # type: ignore[arg-type]
    )
    assert router.capture(
        adapter_code=PUBLIC_ADAPTER,
        permit_id=public_permit,
        external_locator="https://public.example/feed",
        trace_id="trace-route",
        at=NOW,
    ) is public_result
    assert public.calls == 1
    assert credentialed.calls == 0


def test_public_source_acquisition_uses_admission_and_completes_permit_before_write() -> None:
    provider_repository = InMemorySourceProviderAdmissionRepository()
    provider = SourceProviderAdmissionService(provider_repository, clock=lambda: NOW)
    provider.register(
        adapter_code=PUBLIC_ADAPTER,
        credential_mode=ProviderCredentialMode.PUBLIC,
        secret_ref=None,
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=30,
        permit_ttl_seconds=30,
        created_at=NOW,
    )
    public_registry = InMemoryPublicSourceCaptureRegistry((PublicAdapter(),))
    public_executor = PermitBoundPublicCaptureExecutor(
        contexts=provider_repository,
        adapters=public_registry,
    )
    secure_executor = SecureProviderCaptureExecutor(
        contexts=provider_repository,
        resolvers=InMemorySecretResolverRegistry(),
        adapters=InMemoryCredentialAwareSourceCaptureRegistry(),
    )
    router = CredentialModeRoutingProviderCaptureExecutor(
        contexts=provider_repository,
        public_executor=public_executor,
        credentialed_executor=secure_executor,
    )
    knowledge = InMemoryKnowledgeRepository()
    ingestion_repository = InMemoryIngestionOrchestrationRepository()
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=IngestionOrchestrationService(ingestion_repository),
        registry=InMemorySourceCaptureRegistry(),
        observer=NoOpSourceAcquisitionObserver(),
        admission=provider,
        capture_executor=router,
        clock=lambda: NOW,
    )

    result = acquisition.acquire(
        SourceAcquisitionCommand(
            adapter_code=PUBLIC_ADAPTER,
            external_locator="https://public.example/feed",
            pipeline_code="PUBLIC_FEED_CAPTURE",
            pipeline_version="1.0.0",
            configuration_hash="sha256:public-config",
        ),
        trace_id="trace-public-acquisition",
    )

    assert result.outcome is SourceAcquisitionOutcome.ADMITTED
    assert len(knowledge._source_artifacts) == 1
    assert len(ingestion_repository._runs) == 1
    permit = next(iter(provider_repository._permits.values()))
    assert permit.state.value == "SUCCEEDED"


def test_public_registry_rejects_duplicate_adapter_codes() -> None:
    with pytest.raises(ValueError, match="duplicate public"):
        InMemoryPublicSourceCaptureRegistry((PublicAdapter(), PublicAdapter()))
