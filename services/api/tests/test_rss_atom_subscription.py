from __future__ import annotations

from collections import deque
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.in_memory_leases import (
    InMemoryIngestionRunLeaseRepository,
)
from kefe_api.modules.ingestion_orchestration.lease_service import (
    IngestionRunLeaseService,
)
from kefe_api.modules.ingestion_orchestration.models import IngestionRunState
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionWorkerRunOutcome,
    NoOpIngestionWorkerObserver,
)
from kefe_api.modules.ingestion_orchestration.worker_service import (
    IngestionWorkerRunner,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.provider_control import ProviderCredentialMode
from kefe_api.modules.knowledge.provider_control_memory import (
    InMemorySourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    ControlledProviderHttpTransport,
    NoOpProviderHttpObserver,
    RawHttpResponse,
)
from kefe_api.modules.knowledge.provider_public_execution import (
    CredentialModeRoutingProviderCaptureExecutor,
    PermitBoundPublicCaptureExecutor,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapterFactory,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    InMemoryCredentialAwareSourceCaptureRegistry,
    InMemorySecretResolverRegistry,
    SecureProviderCaptureExecutor,
)
from kefe_api.modules.knowledge.rss_atom_subscription import (
    RssAtomSubscriptionActivationService,
    RssAtomSubscriptionManifest,
    RssAtomSubscriptionManifestRegistry,
    build_rss_atom_ingestion_worker_registry,
    build_rss_atom_provider_adoption_registry,
    build_rss_atom_public_capture_registry,
)
from kefe_api.modules.knowledge.source_acquisition import (
    InMemorySourceCaptureRegistry,
    NoOpSourceAcquisitionObserver,
    SourceAcquisitionService,
)
from kefe_api.modules.knowledge.source_evidence import (
    InMemoryRawSourceEvidenceStore,
)
from kefe_api.modules.knowledge.source_scheduler_memory import (
    InMemorySourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    NoOpSourceDispatchObserver,
    SourceAcquisitionSchedulerService,
    SourceDispatchExecutionOutcome,
)

NOW = datetime(2026, 8, 3, 14, 0, tzinfo=UTC)
ADAPTER_CODE = "test.rss_atom_provider.v1"
SUBSCRIPTION_CODE = "test.rss_atom_subscription.v1"
FEED_URL = "https://feeds.example.test/news.xml"

RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example News</title>
    <link>https://www.example.test/news</link>
    <description>Example feed snapshot</description>
    <lastBuildDate>Mon, 03 Aug 2026 13:50:00 GMT</lastBuildDate>
    <item>
      <guid>item-1</guid>
      <title>First item</title>
      <link>https://www.example.test/news/first</link>
      <pubDate>Mon, 03 Aug 2026 13:45:00 GMT</pubDate>
      <description>First summary</description>
    </item>
  </channel>
</rss>
"""


def _manifest(**overrides) -> RssAtomSubscriptionManifest:
    values = {
        "subscription_code": SUBSCRIPTION_CODE,
        "adapter_code": ADAPTER_CODE,
        "external_locator": FEED_URL,
        "interval_seconds": 300,
        "max_dispatch_attempts": 3,
        "quota_limit": 20,
        "quota_window_seconds": 60,
        "failure_threshold": 3,
        "circuit_open_seconds": 30,
        "permit_ttl_seconds": 30,
        "connect_timeout_ms": 500,
        "read_timeout_ms": 1500,
        "total_timeout_ms": 2500,
        "max_redirect_hops": 1,
        "terms_evidence_ref": "docref://providers/example/terms-v1",
        "rate_limit_evidence_ref": "evidence://providers/example/rate-v1",
        "locale": "en-US",
        "jurisdiction_code": "US",
    }
    values.update(overrides)
    return RssAtomSubscriptionManifest(**values)


class FakeDnsResolver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def resolve(self, host: str) -> tuple[str, ...]:
        self.calls.append(host)
        return ("8.8.8.8",)


class FakeBackend:
    def __init__(self, outcomes) -> None:
        self.outcomes = deque(outcomes)
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        outcome = self.outcomes.popleft()
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class FailOnceScheduler:
    def __init__(self, inner: SourceAcquisitionSchedulerService) -> None:
        self.inner = inner
        self.calls = 0

    def create_schedule(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("simulated schedule persistence failure")
        return self.inner.create_schedule(**kwargs)


def _raw_response() -> RawHttpResponse:
    return RawHttpResponse(
        status_code=200,
        headers=(("content-type", "application/rss+xml; charset=utf-8"),),
        body=RSS_BODY,
        elapsed_ms=10,
    )


def _activation_services(registry: RssAtomSubscriptionManifestRegistry):
    provider_repository = InMemorySourceProviderAdmissionRepository()
    provider_service = SourceProviderAdmissionService(
        provider_repository,
        clock=lambda: NOW,
    )
    ingestion_repository = InMemoryIngestionOrchestrationRepository()
    ingestion_service = IngestionOrchestrationService(ingestion_repository)
    acquisition = SourceAcquisitionService(
        knowledge_repository=InMemoryKnowledgeRepository(),
        ingestion_service=ingestion_service,
        registry=InMemorySourceCaptureRegistry(),
        observer=NoOpSourceAcquisitionObserver(),
    )
    scheduler_repository = InMemorySourceAcquisitionSchedulerRepository()
    scheduler_service = SourceAcquisitionSchedulerService(
        repository=scheduler_repository,
        acquisition=acquisition,
        observer=NoOpSourceDispatchObserver(),
        clock=lambda: NOW,
    )
    activation = RssAtomSubscriptionActivationService(
        registry=registry,
        admission=provider_service,
        scheduler=scheduler_service,
    )
    return (
        provider_repository,
        provider_service,
        scheduler_repository,
        scheduler_service,
        activation,
    )


def test_manifest_is_immutable_canonical_and_hash_stable() -> None:
    manifest = _manifest()
    same = _manifest()

    assert manifest.origin == "https://feeds.example.test"
    assert manifest.configuration_hash == same.configuration_hash
    assert manifest.configuration_hash.startswith("sha256:")
    assert len(manifest.configuration_hash) == 71
    with pytest.raises(FrozenInstanceError):
        manifest.interval_seconds = 600  # type: ignore[misc]

    for invalid_locator in (
        "http://feeds.example.test/news.xml",
        "https://User@feeds.example.test/news.xml",
        "https://FEEDS.example.test/news.xml",
        "https://feeds.example.test:443/news.xml",
        "https://feeds.example.test/news.xml#fragment",
        "https://feeds.example.test/news.xml?token=secret",
        "https://feeds.example.test/news.xml?z=1&a=2",
    ):
        with pytest.raises(ValueError):
            _manifest(external_locator=invalid_locator)


def test_registry_groups_shared_adapter_and_rejects_policy_drift() -> None:
    first = _manifest()
    second = _manifest(
        subscription_code="test.rss_atom_subscription_two.v1",
        external_locator="https://alerts.example.test/feed.xml",
        interval_seconds=600,
        locale="tr-TR",
        jurisdiction_code="TR",
    )
    registry = RssAtomSubscriptionManifestRegistry((second, first))

    assert registry.manifests == (first, second)
    assert registry.adapter_codes == (ADAPTER_CODE,)
    assert registry.for_adapter(ADAPTER_CODE) == (first, second)

    with pytest.raises(ValueError, match="policy drift"):
        RssAtomSubscriptionManifestRegistry(
            (first, _manifest(
                subscription_code="test.policy_drift.v1",
                external_locator="https://other.example.test/feed.xml",
                quota_limit=21,
            ))
        )
    with pytest.raises(ValueError, match="adapter locator"):
        RssAtomSubscriptionManifestRegistry(
            (first, _manifest(subscription_code="test.duplicate_locator.v1"))
        )


def test_component_assembly_derives_exact_origins_and_existing_runtime() -> None:
    first = _manifest()
    second = _manifest(
        subscription_code="test.rss_atom_subscription_two.v1",
        external_locator="https://alerts.example.test/feed.xml",
    )
    registry = RssAtomSubscriptionManifestRegistry((first, second))
    evidence = InMemoryRawSourceEvidenceStore()
    transport = ControlledProviderHttpTransport(
        adoption_registry=build_rss_atom_provider_adoption_registry(registry),
        dns_resolver=FakeDnsResolver(),
        backend=FakeBackend((_raw_response(),)),
        observer=NoOpProviderHttpObserver(),
    )
    factory = EvidenceBackedPublicHttpCaptureAdapterFactory(
        transport=transport,
        evidence_store=evidence,
    )
    public = build_rss_atom_public_capture_registry(
        registry=registry,
        factory=factory,
    )
    ingestion = build_rss_atom_ingestion_worker_registry(
        registry=registry,
        knowledge=InMemoryKnowledgeRepository(),
        evidence=evidence,
    )
    adoption = build_rss_atom_provider_adoption_registry(registry).get(ADAPTER_CODE)

    assert adoption.allowed_origins == (
        "https://alerts.example.test",
        "https://feeds.example.test",
    )
    assert adoption.allowed_methods[0].value == "GET"
    assert adoption.max_response_bytes == 1_048_576
    assert public.get(ADAPTER_CODE).adapter_code == ADAPTER_CODE
    plan = ingestion.get_plan(
        pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
        pipeline_version="1.0.0",
    )
    assert plan.stages[0].stage_code == "EXTRACT_FEED_ITEMS"


def test_empty_registry_builds_zero_runtime_components() -> None:
    registry = RssAtomSubscriptionManifestRegistry()
    evidence = InMemoryRawSourceEvidenceStore()
    adoption = build_rss_atom_provider_adoption_registry(registry)
    transport = ControlledProviderHttpTransport(
        adoption_registry=adoption,
        dns_resolver=FakeDnsResolver(),
        backend=FakeBackend(()),
        observer=NoOpProviderHttpObserver(),
    )
    public = build_rss_atom_public_capture_registry(
        registry=registry,
        factory=EvidenceBackedPublicHttpCaptureAdapterFactory(
            transport=transport,
            evidence_store=evidence,
        ),
    )
    ingestion = build_rss_atom_ingestion_worker_registry(
        registry=registry,
        knowledge=InMemoryKnowledgeRepository(),
        evidence=evidence,
    )

    assert len(registry) == 0
    with pytest.raises(KeyError):
        adoption.get(ADAPTER_CODE)
    with pytest.raises(KeyError):
        public.get(ADAPTER_CODE)
    with pytest.raises(KeyError):
        ingestion.get_plan(
            pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
            pipeline_version="1.0.0",
        )


def test_activation_orders_public_capability_before_schedule_and_is_idempotent() -> None:
    registry = RssAtomSubscriptionManifestRegistry((_manifest(),))
    provider_repository, _, _, _, activation = _activation_services(registry)

    first = activation.activate(
        subscription_code=SUBSCRIPTION_CODE,
        first_due_at=NOW,
        activated_at=NOW,
    )
    second = activation.activate(
        subscription_code=SUBSCRIPTION_CODE,
        first_due_at=NOW,
        activated_at=NOW,
    )

    capability = provider_repository.get(ADAPTER_CODE)
    assert capability is not None
    assert capability.credential_mode is ProviderCredentialMode.PUBLIC
    assert capability.secret_ref is None
    assert first.provider_capability == second.provider_capability
    assert first.schedule.id == second.schedule.id
    assert first.schedule.configuration_hash == _manifest().configuration_hash


def test_activation_failure_leaves_only_inert_capability_and_retries_cleanly() -> None:
    registry = RssAtomSubscriptionManifestRegistry((_manifest(),))
    (
        provider_repository,
        provider_service,
        _,
        scheduler_service,
        _,
    ) = _activation_services(registry)
    fail_once = FailOnceScheduler(scheduler_service)
    activation = RssAtomSubscriptionActivationService(
        registry=registry,
        admission=provider_service,
        scheduler=fail_once,  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeError, match="schedule persistence"):
        activation.activate(
            subscription_code=SUBSCRIPTION_CODE,
            first_due_at=NOW,
            activated_at=NOW,
        )
    capability = provider_repository.get(ADAPTER_CODE)
    assert capability is not None
    assert capability.credential_mode is ProviderCredentialMode.PUBLIC

    completed = activation.activate(
        subscription_code=SUBSCRIPTION_CODE,
        first_due_at=NOW,
        activated_at=NOW,
    )
    assert completed.schedule.adapter_code == ADAPTER_CODE
    assert fail_once.calls == 2


def test_complete_scheduled_capture_to_feed_item_worker_vertical_path() -> None:
    manifest = _manifest()
    registry = RssAtomSubscriptionManifestRegistry((manifest,))
    knowledge = InMemoryKnowledgeRepository()
    evidence = InMemoryRawSourceEvidenceStore()
    provider_repository = InMemorySourceProviderAdmissionRepository()
    provider_service = SourceProviderAdmissionService(
        provider_repository,
        clock=lambda: NOW,
    )
    adoption = build_rss_atom_provider_adoption_registry(registry)
    resolver = FakeDnsResolver()
    backend = FakeBackend((_raw_response(),))
    transport = ControlledProviderHttpTransport(
        adoption_registry=adoption,
        dns_resolver=resolver,
        backend=backend,
        observer=NoOpProviderHttpObserver(),
        monotonic_clock=lambda: 0,
    )
    factory = EvidenceBackedPublicHttpCaptureAdapterFactory(
        transport=transport,
        evidence_store=evidence,
    )
    public_registry = build_rss_atom_public_capture_registry(
        registry=registry,
        factory=factory,
    )
    public_executor = PermitBoundPublicCaptureExecutor(
        contexts=provider_repository,
        adapters=public_registry,
    )
    secure_executor = SecureProviderCaptureExecutor(
        contexts=provider_repository,
        resolvers=InMemorySecretResolverRegistry(),
        adapters=InMemoryCredentialAwareSourceCaptureRegistry(),
    )
    capture_executor = CredentialModeRoutingProviderCaptureExecutor(
        contexts=provider_repository,
        public_executor=public_executor,
        credentialed_executor=secure_executor,
    )

    ingestion_repository = InMemoryIngestionOrchestrationRepository()
    ingestion_service = IngestionOrchestrationService(ingestion_repository)
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=ingestion_service,
        registry=InMemorySourceCaptureRegistry(),
        observer=NoOpSourceAcquisitionObserver(),
        admission=provider_service,
        capture_executor=capture_executor,
        clock=lambda: NOW,
        monotonic_clock=lambda: 0,
    )
    scheduler_repository = InMemorySourceAcquisitionSchedulerRepository()
    scheduler = SourceAcquisitionSchedulerService(
        repository=scheduler_repository,
        acquisition=acquisition,
        observer=NoOpSourceDispatchObserver(),
        clock=lambda: NOW,
        monotonic_clock=lambda: 0,
    )
    activation = RssAtomSubscriptionActivationService(
        registry=registry,
        admission=provider_service,
        scheduler=scheduler,
    )
    activation.activate(
        subscription_code=SUBSCRIPTION_CODE,
        first_due_at=NOW,
        activated_at=NOW,
    )

    dispatch = scheduler.plan_due_once(now=NOW)
    assert dispatch is not None
    execution = scheduler.execute_pending_once(
        worker_ref="subscription-worker",
        ttl_seconds=30,
        trace_id="trace-subscription",
        now=NOW,
    )
    assert execution.outcome is SourceDispatchExecutionOutcome.SUCCEEDED
    assert execution.source_artifact_id is not None
    assert execution.ingestion_run_id is not None
    assert resolver.calls == ["feeds.example.test"]
    assert len(backend.requests) == 1
    assert evidence.object_count == 1

    run = ingestion_repository.get_run(execution.ingestion_run_id)
    assert run is not None
    assert run.state is IngestionRunState.QUEUED
    assert run.configuration_hash == manifest.configuration_hash
    worker_registry = build_rss_atom_ingestion_worker_registry(
        registry=registry,
        knowledge=knowledge,
        evidence=evidence,
    )
    lease_repository = InMemoryIngestionRunLeaseRepository(ingestion_repository)
    worker = IngestionWorkerRunner(
        repository=ingestion_repository,
        orchestration=ingestion_service,
        leases=IngestionRunLeaseService(lease_repository),
        registry=worker_registry,
        observer=NoOpIngestionWorkerObserver(),
        clock=lambda: NOW,
        monotonic_clock=lambda: 0,
    )
    result = worker.run_once(
        worker_ref="feed-item-worker",
        pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
        pipeline_version="1.0.0",
        ttl_seconds=30,
        trace_id="trace-feed-items",
    )

    assert result.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    proposals = ingestion_repository.list_proposals(run.id)
    assert len(proposals) == 1
    assert proposals[0].proposal_kind == "FEED_ITEM"
    assert proposals[0].payload["item_id"] == "item-1"
    assert ingestion_repository.get_review_decision(proposals[0].id) is None
    assert ingestion_repository.find_materialization(proposals[0].id) is None


def test_production_pipeline_composes_empty_registry_without_activation() -> None:
    from kefe_api.main import app

    registry = app.state.rss_atom_subscription_registry
    assert len(registry) == 0
    with pytest.raises(KeyError):
        app.state.provider_adoption_registry.get(ADAPTER_CODE)
    with pytest.raises(KeyError):
        app.state.public_capture_registry.get(ADAPTER_CODE)
    with pytest.raises(KeyError):
        app.state.ingestion_worker_runtime_registry.get_plan(
            pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
            pipeline_version="1.0.0",
        )
