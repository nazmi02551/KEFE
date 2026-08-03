from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID

import pytest

from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PIPELINE_CODE,
    PIPELINE_VERSION,
    PROPOSAL_KIND,
    FeedItemExtractionStageProcessor,
    build_feed_item_extraction_runtime,
)
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.in_memory_leases import (
    InMemoryIngestionRunLeaseRepository,
)
from kefe_api.modules.ingestion_orchestration.lease_service import (
    IngestionRunLeaseService,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)
from kefe_api.modules.ingestion_orchestration.worker_runtime import (
    IngestionWorkerRunOutcome,
    InMemoryIngestionWorkerObserver,
)
from kefe_api.modules.ingestion_orchestration.worker_service import (
    IngestionWorkerRunner,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.provider_control import (
    ProviderCapabilityLifecycle,
    ProviderCredentialMode,
    SourceProviderCapability,
)
from kefe_api.modules.knowledge.provider_control_memory import (
    InMemorySourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.provider_http_transport import (
    InMemoryProviderHttpObserver,
    ProviderAdoptionProfile,
    ProviderHttpMethod,
    RawHttpResponse,
)
from kefe_api.modules.knowledge.provider_public_execution import (
    CredentialModeRoutingProviderCaptureExecutor,
    PermitBoundPublicCaptureExecutor,
)
from kefe_api.modules.knowledge.provider_secret_execution import (
    InMemoryCredentialAwareSourceCaptureRegistry,
    InMemorySecretResolverRegistry,
    SecureProviderCaptureExecutor,
)
from kefe_api.modules.knowledge.public_feed_activation import (
    InMemoryPublicFeedActivationRegistry,
    PublicFeedActivationBundleFactory,
    PublicFeedActivationDefinition,
)
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile
from kefe_api.modules.knowledge.source_acquisition import (
    InMemorySourceAcquisitionObserver,
    InMemorySourceCaptureRegistry,
    SourceAcquisitionService,
)
from kefe_api.modules.knowledge.source_evidence import (
    InMemoryRawSourceEvidenceStore,
    canonical_content_hash,
)
from kefe_api.modules.knowledge.source_scheduler_memory import (
    InMemorySourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    InMemorySourceDispatchObserver,
    SourceAcquisitionSchedulerService,
    SourceDispatchExecutionOutcome,
)

NOW = datetime(2026, 8, 3, 8, 0, tzinfo=UTC)
ACTIVATION_CODE = "test.public_feed_activation.v1"
ADAPTER_CODE = "test.public_feed_adapter.v1"
FEED_URL = "https://feeds.example.test/news.xml?edition=global"

RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Activation Feed</title>
    <link>https://www.example.test/news</link>
    <description>Activation integration fixture.</description>
    <lastBuildDate>Mon, 03 Aug 2026 07:50:00 GMT</lastBuildDate>
    <item>
      <guid>item-b</guid>
      <title>Second item</title>
      <link>https://www.example.test/news/b</link>
      <pubDate>Mon, 03 Aug 2026 07:40:00 GMT</pubDate>
      <description>Second summary.</description>
    </item>
    <item>
      <guid>item-a</guid>
      <title>First item</title>
      <link>https://www.example.test/news/a</link>
      <pubDate>Mon, 03 Aug 2026 07:30:00 GMT</pubDate>
      <description>First summary.</description>
    </item>
  </channel>
</rss>
"""


class FakeDnsResolver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def resolve(self, host: str) -> tuple[str, ...]:
        self.calls.append(host)
        return ("8.8.8.8",)


class FakePinnedBackend:
    def __init__(self, body: bytes = RSS_BODY) -> None:
        self.body = body
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return RawHttpResponse(
            status_code=200,
            headers=(("content-type", "application/rss+xml; charset=utf-8"),),
            body=self.body,
            elapsed_ms=9,
        )


def _parser(**overrides) -> StrictRssAtomParseProfile:
    values = {
        "max_document_bytes": 4096,
        "max_items": 32,
    }
    values.update(overrides)
    return StrictRssAtomParseProfile(**values)


def _adoption(
    *,
    adapter_code: str = ADAPTER_CODE,
    parser: StrictRssAtomParseProfile | None = None,
    allowed_origins: tuple[str, ...] = ("https://feeds.example.test",),
    allowed_methods: tuple[ProviderHttpMethod, ...] = (ProviderHttpMethod.GET,),
    allowed_media_types: tuple[str, ...] | None = None,
    max_response_bytes: int | None = None,
) -> ProviderAdoptionProfile:
    resolved = parser or _parser()
    return ProviderAdoptionProfile(
        adapter_code=adapter_code,
        allowed_origins=allowed_origins,
        allowed_methods=allowed_methods,
        allowed_media_types=(
            resolved.accepted_media_types
            if allowed_media_types is None
            else allowed_media_types
        ),
        connect_timeout_ms=200,
        read_timeout_ms=500,
        total_timeout_ms=1000,
        max_response_bytes=(
            resolved.max_document_bytes
            if max_response_bytes is None
            else max_response_bytes
        ),
        max_redirect_hops=1,
        terms_evidence_ref="docref://feeds/example/terms-v1",
        rate_limit_evidence_ref="evidence://feeds/example/rate-limit-v1",
    )


def _capability(
    *,
    adapter_code: str = ADAPTER_CODE,
    credential_mode: ProviderCredentialMode = ProviderCredentialMode.PUBLIC,
    secret_ref: str | None = None,
) -> SourceProviderCapability:
    return SourceProviderCapability.create(
        adapter_code=adapter_code,
        credential_mode=credential_mode,
        secret_ref=secret_ref,
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=60,
        permit_ttl_seconds=30,
        created_at=NOW,
    )


def _activation(
    *,
    activation_code: str = ACTIVATION_CODE,
    adapter_code: str = ADAPTER_CODE,
    external_locator: str = FEED_URL,
    parser: StrictRssAtomParseProfile | None = None,
    adoption: ProviderAdoptionProfile | None = None,
    capability: SourceProviderCapability | None = None,
    interval_seconds: int = 300,
) -> PublicFeedActivationDefinition:
    resolved_parser = parser or _parser()
    return PublicFeedActivationDefinition(
        activation_code=activation_code,
        adapter_code=adapter_code,
        external_locator=external_locator,
        adoption_profile=adoption or _adoption(parser=resolved_parser),
        parser_profile=resolved_parser,
        capability=capability or _capability(adapter_code=adapter_code),
        first_due_at=NOW,
        interval_seconds=interval_seconds,
        max_dispatch_attempts=3,
        locale="en",
        jurisdiction_code="GLOBAL",
    )


def _bundle(
    definition: PublicFeedActivationDefinition,
    *,
    evidence: InMemoryRawSourceEvidenceStore | None = None,
):
    dns = FakeDnsResolver()
    backend = FakePinnedBackend()
    observer = InMemoryProviderHttpObserver()
    evidence_store = evidence or InMemoryRawSourceEvidenceStore()
    bundle = PublicFeedActivationBundleFactory(
        dns_resolver=dns,
        backend=backend,
        observer=observer,
        evidence_store=evidence_store,
        monotonic_clock=lambda: 0,
    ).build((definition,))
    return bundle, dns, backend, observer, evidence_store


def test_activation_is_immutable_and_configuration_hash_is_canonical() -> None:
    definition = _activation()
    same = _activation()
    changed = _activation(interval_seconds=600)

    assert definition.configuration_hash == same.configuration_hash
    assert definition.configuration_hash.startswith("sha256:")
    assert len(definition.configuration_hash) == 71
    assert changed.configuration_hash != definition.configuration_hash
    assert definition.schedule_seed().configuration_hash == definition.configuration_hash
    assert definition.configuration_payload["schedule"] == {
        "pipeline_code": PIPELINE_CODE,
        "pipeline_version": PIPELINE_VERSION,
        "first_due_at": NOW.isoformat(),
        "interval_seconds": 300,
        "max_dispatch_attempts": 3,
        "taxonomy_version": None,
        "methodology_version": None,
        "locale": "en",
        "jurisdiction_code": "GLOBAL",
    }
    with pytest.raises(FrozenInstanceError):
        definition.interval_seconds = 1  # type: ignore[misc]


def test_activation_rejects_identity_policy_parser_and_locator_drift() -> None:
    parser = _parser()
    with pytest.raises(ValueError, match="adapter identity"):
        _activation(adoption=_adoption(adapter_code="test.other.v1", parser=parser))
    with pytest.raises(ValueError, match="exact feed origin"):
        _activation(
            adoption=_adoption(
                parser=parser,
                allowed_origins=(
                    "https://feeds.example.test",
                    "https://other.example.test",
                ),
            )
        )
    with pytest.raises(ValueError, match="GET-only"):
        _activation(
            adoption=_adoption(
                parser=parser,
                allowed_methods=(ProviderHttpMethod.GET, ProviderHttpMethod.HEAD),
            )
        )
    with pytest.raises(ValueError, match="media types"):
        _activation(
            adoption=_adoption(
                parser=parser,
                allowed_media_types=("application/rss+xml",),
            )
        )
    with pytest.raises(ValueError, match="byte budgets"):
        _activation(adoption=_adoption(parser=parser, max_response_bytes=2048))
    with pytest.raises(ValueError, match="proposal budget"):
        oversized = _parser(max_items=257)
        _activation(parser=oversized, adoption=_adoption(parser=oversized))
    with pytest.raises(ValueError, match="credential-like"):
        _activation(external_locator="https://feeds.example.test/news.xml?api-key=x")
    with pytest.raises(ValueError, match="https"):
        _activation(external_locator="http://feeds.example.test/news.xml")


def test_activation_requires_clean_public_secret_free_capability() -> None:
    with pytest.raises(ValueError, match="PUBLIC"):
        _activation(
            capability=_capability(
                credential_mode=ProviderCredentialMode.SECRET_REF,
                secret_ref="secret://feeds/token-v1",
            )
        )
    paused = _capability().transition_lifecycle(
        ProviderCapabilityLifecycle.PAUSED,
        at=NOW,
    )
    with pytest.raises(ValueError, match="ENABLED"):
        _activation(capability=paused)


def test_registry_and_bundle_reject_duplicate_activation_or_adapter() -> None:
    definition = _activation()
    with pytest.raises(ValueError, match="duplicate public feed activation"):
        InMemoryPublicFeedActivationRegistry((definition, definition))

    same_adapter = _activation(
        activation_code="test.public_feed_activation_two.v1",
    )
    with pytest.raises(ValueError, match="duplicate public feed adapter"):
        InMemoryPublicFeedActivationRegistry((definition, same_adapter))

    empty = PublicFeedActivationBundleFactory(
        dns_resolver=FakeDnsResolver(),
        backend=FakePinnedBackend(),
        observer=InMemoryProviderHttpObserver(),
        evidence_store=InMemoryRawSourceEvidenceStore(),
        monotonic_clock=lambda: 0,
    ).build()
    with pytest.raises(KeyError):
        empty.activation_registry.get(ACTIVATION_CODE)
    with pytest.raises(KeyError):
        empty.adoption_registry.get(ADAPTER_CODE)
    with pytest.raises(KeyError):
        empty.public_capture_registry.get(ADAPTER_CODE)
    assert empty.capabilities == ()
    assert empty.schedule_seeds == ()


def test_bundle_uses_one_exact_adoption_registry_for_controlled_transport() -> None:
    definition = _activation()
    bundle, dns, backend, observer, evidence = _bundle(definition)

    assert bundle.activation_registry.get(ACTIVATION_CODE) is definition
    assert bundle.activation_registry.get_by_adapter(ADAPTER_CODE) is definition
    assert bundle.adoption_registry.get(ADAPTER_CODE) is definition.adoption_profile
    assert bundle.public_capture_registry.get(ADAPTER_CODE).adapter_code == ADAPTER_CODE
    assert bundle.capabilities == (definition.capability,)
    assert bundle.schedule_seeds[0].configuration_hash == definition.configuration_hash
    assert dns.calls == []
    assert backend.requests == []
    assert observer.results == []
    assert evidence.object_count == 0


def test_full_schedule_to_capture_to_ingestion_worker_vertical_path() -> None:
    definition = _activation()
    evidence = InMemoryRawSourceEvidenceStore()
    bundle, dns, backend, http_observer, _ = _bundle(
        definition,
        evidence=evidence,
    )

    provider_repository = InMemorySourceProviderAdmissionRepository()
    for capability in bundle.capabilities:
        provider_repository.create_or_get(capability)
    provider_admission = SourceProviderAdmissionService(provider_repository)

    public_executor = PermitBoundPublicCaptureExecutor(
        contexts=provider_repository,
        adapters=bundle.public_capture_registry,
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

    knowledge = InMemoryKnowledgeRepository()
    ingestion_repository = InMemoryIngestionOrchestrationRepository()
    ingestion = IngestionOrchestrationService(ingestion_repository)
    acquisition_observer = InMemorySourceAcquisitionObserver()
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=ingestion,
        registry=InMemorySourceCaptureRegistry(),
        observer=acquisition_observer,
        admission=provider_admission,
        capture_executor=capture_executor,
        clock=lambda: NOW,
        monotonic_clock=lambda: 0,
    )

    scheduler_repository = InMemorySourceAcquisitionSchedulerRepository()
    dispatch_observer = InMemorySourceDispatchObserver()
    scheduler = SourceAcquisitionSchedulerService(
        repository=scheduler_repository,
        acquisition=acquisition,
        observer=dispatch_observer,
        clock=lambda: NOW,
        monotonic_clock=lambda: 0,
    )
    schedule = bundle.schedule_seeds[0].install(scheduler, now=NOW)
    dispatch = scheduler.plan_due_once(now=NOW)
    assert dispatch is not None

    dispatched = scheduler.execute_pending_once(
        worker_ref="feed-dispatcher",
        ttl_seconds=30,
        trace_id="trace-public-feed-activation",
        now=NOW,
    )
    assert dispatched.outcome is SourceDispatchExecutionOutcome.SUCCEEDED
    assert dispatched.schedule_id == schedule.id
    assert isinstance(dispatched.source_artifact_id, UUID)
    assert isinstance(dispatched.ingestion_run_id, UUID)
    assert dns.calls == ["feeds.example.test"]
    assert len(backend.requests) == 1
    pinned = backend.requests[0]
    assert pinned.host == "feeds.example.test"
    assert pinned.port == 443
    assert pinned.target_ip == "8.8.8.8"
    assert pinned.request_target == "/news.xml?edition=global"
    assert pinned.sensitive_headers is None
    assert http_observer.results[-1].error_code is None
    assert evidence.object_count == 1

    artifact = knowledge.get_source_artifact(dispatched.source_artifact_id)
    assert artifact is not None
    assert artifact.content_hash == canonical_content_hash(RSS_BODY)
    assert artifact.raw_storage_ref is not None
    assert artifact.canonical_url == FEED_URL
    assert artifact.publisher_or_issuer == "Activation Feed"

    feed_processor = FeedItemExtractionStageProcessor(
        knowledge=knowledge,
        evidence=evidence,
    )
    lease_repository = InMemoryIngestionRunLeaseRepository(ingestion_repository)
    worker_observer = InMemoryIngestionWorkerObserver()
    worker = IngestionWorkerRunner(
        repository=ingestion_repository,
        orchestration=ingestion,
        leases=IngestionRunLeaseService(lease_repository),
        registry=build_feed_item_extraction_runtime(feed_processor),
        observer=worker_observer,
        clock=lambda: NOW,
        monotonic_clock=lambda: 0,
    )
    worked = worker.run_once(
        worker_ref="feed-item-worker",
        pipeline_code=PIPELINE_CODE,
        pipeline_version=PIPELINE_VERSION,
        ttl_seconds=30,
        trace_id="trace-feed-item-worker",
    )
    assert worked.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    assert worked.run_id == dispatched.ingestion_run_id
    proposals = ingestion_repository.list_proposals(dispatched.ingestion_run_id)
    assert sorted(item.payload["item_id"] for item in proposals) == [
        "item-a",
        "item-b",
    ]
    assert all(item.proposal_kind == PROPOSAL_KIND for item in proposals)
    assert all(
        ingestion_repository.get_review_decision(item.id) is None
        for item in proposals
    )
    assert all(
        ingestion_repository.find_materialization(item.id) is None
        for item in proposals
    )
    capability = provider_repository.get(ADAPTER_CODE)
    assert capability is not None
    assert capability.window_request_count == 1
    assert capability.consecutive_failure_count == 0
    assert acquisition_observer.results[-1].error_code is None
    assert dispatch_observer.results[-1].error_code is None
    assert worker_observer.results[-1].error_code is None
