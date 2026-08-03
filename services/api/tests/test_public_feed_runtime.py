from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PIPELINE_CODE,
    PIPELINE_VERSION,
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
    ProviderHttpMethod,
    ProviderHttpResponse,
)
from kefe_api.modules.knowledge.provider_public_execution import (
    PermitBoundPublicCaptureExecutor,
)
from kefe_api.modules.knowledge.provider_public_http_capture import (
    EvidenceBackedPublicHttpCaptureAdapterFactory,
)
from kefe_api.modules.knowledge.public_feed_runtime import (
    InMemoryPublicFeedDefinitionRegistry,
    ManualPublicFeedCaptureService,
    PublicFeedDefinition,
    PublicFeedRuntimeError,
    build_public_feed_runtime_bundle,
)
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile
from kefe_api.modules.knowledge.source_acquisition import (
    InMemorySourceCaptureRegistry,
    NoOpSourceAcquisitionObserver,
    SourceAcquisitionOutcome,
    SourceAcquisitionResult,
    SourceAcquisitionService,
)
from kefe_api.modules.knowledge.source_evidence import InMemoryRawSourceEvidenceStore

AT = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)
RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Public Feed</title>
    <link>https://publisher.example.test/</link>
    <description>Example feed description.</description>
    <language>en</language>
    <lastBuildDate>Mon, 03 Aug 2026 12:00:00 GMT</lastBuildDate>
    <item>
      <guid>item-001</guid>
      <title>First item</title>
      <link>https://publisher.example.test/items/1</link>
      <pubDate>Mon, 03 Aug 2026 11:30:00 GMT</pubDate>
      <description>First item summary.</description>
    </item>
  </channel>
</rss>
"""


def _definition(**overrides) -> PublicFeedDefinition:
    values = {
        "feed_code": "test.public_feed.v1",
        "display_name": "Example Public Feed",
        "adapter_code": "test.public_rss.v1",
        "external_locator": "https://feeds.example.test/news.xml",
        "parser_profile": StrictRssAtomParseProfile(),
        "connect_timeout_ms": 1000,
        "read_timeout_ms": 1500,
        "total_timeout_ms": 3000,
        "max_response_bytes": 1_048_576,
        "max_redirect_hops": 2,
        "terms_evidence_ref": "evidence://terms/public-feed-v1",
        "rate_limit_evidence_ref": "evidence://rate/public-feed-v1",
        "quota_limit": 20,
        "quota_window_seconds": 60,
        "failure_threshold": 3,
        "circuit_open_seconds": 120,
        "permit_ttl_seconds": 30,
        "language_code": "en",
        "jurisdiction_code": "GLOBAL",
    }
    values.update(overrides)
    return PublicFeedDefinition(**values)


class FakeTransport:
    def __init__(self, body: bytes = RSS_BODY) -> None:
        self.body = body
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return ProviderHttpResponse(
            status_code=200,
            media_type="application/rss+xml",
            body=self.body,
            redirect_hops=0,
            elapsed_ms=12,
        )


class RecordingAcquisition:
    def __init__(self) -> None:
        self.calls = []

    def acquire(self, command, *, trace_id=None):
        self.calls.append((command, trace_id))
        return SourceAcquisitionResult(
            outcome=SourceAcquisitionOutcome.BLOCKED,
            adapter_code=command.adapter_code,
            pipeline_code=command.pipeline_code,
            pipeline_version=command.pipeline_version,
            trace_id=trace_id or "generated",
            duration_ms=0,
            error_code="TEST_BLOCKED",
        )


def test_definition_derives_exact_public_profiles_and_stable_command() -> None:
    definition = _definition()
    profile = definition.to_adoption_profile()
    capability = definition.capability_template.instantiate(created_at=AT)
    command = definition.acquisition_command()

    assert definition.origin == "https://feeds.example.test"
    assert profile.adapter_code == definition.adapter_code
    assert profile.allowed_origins == (definition.origin,)
    assert profile.allowed_methods == (ProviderHttpMethod.GET,)
    assert profile.allowed_media_types == definition.parser_profile.accepted_media_types
    assert capability.credential_mode is ProviderCredentialMode.PUBLIC
    assert capability.secret_ref is None
    assert command.adapter_code == definition.adapter_code
    assert command.external_locator == definition.external_locator
    assert command.pipeline_code == PIPELINE_CODE
    assert command.pipeline_version == PIPELINE_VERSION
    assert command.configuration_hash == definition.configuration_hash
    assert definition.configuration_hash.startswith("sha256:")
    assert len(definition.configuration_hash) == 71


@pytest.mark.parametrize(
    "external_locator",
    [
        "http://feeds.example.test/news.xml",
        "https://user:pass@feeds.example.test/news.xml",
        "https://feeds.example.test:8443/news.xml",
        "https://feeds.example.test/news.xml#fragment",
        "https://feeds.example.test/news.xml?access-token=private",
        "https://feeds.example.test/news.xml?signature=private",
    ],
)
def test_definition_rejects_unsafe_locator_forms(external_locator: str) -> None:
    with pytest.raises(ValueError):
        _definition(external_locator=external_locator)


def test_registry_rejects_order_duplicates_and_adapter_conflicts() -> None:
    first = _definition()
    second = _definition(
        feed_code="test.second_feed.v1",
        adapter_code="test.second_rss.v1",
        external_locator="https://second.example.test/feed.xml",
    )
    registry = InMemoryPublicFeedDefinitionRegistry((first, second))
    assert registry.get(first.feed_code) is first

    with pytest.raises(ValueError, match="sorted"):
        InMemoryPublicFeedDefinitionRegistry((second, first))
    with pytest.raises(ValueError, match="feed code"):
        InMemoryPublicFeedDefinitionRegistry((first, first))
    with pytest.raises(ValueError, match="adapter code"):
        InMemoryPublicFeedDefinitionRegistry(
            (
                first,
                _definition(
                    feed_code="test.third_feed.v1",
                    external_locator="https://third.example.test/feed.xml",
                ),
            )
        )


def test_manual_service_emits_one_exact_acquisition_command() -> None:
    definition = _definition()
    recording = RecordingAcquisition()
    service = ManualPublicFeedCaptureService(
        definitions=InMemoryPublicFeedDefinitionRegistry((definition,)),
        acquisition=recording,
    )

    result = service.capture_once(
        feed_code=definition.feed_code,
        trace_id="trace-manual-feed",
    )

    assert result.outcome is SourceAcquisitionOutcome.BLOCKED
    assert len(recording.calls) == 1
    command, trace_id = recording.calls[0]
    assert command == definition.acquisition_command()
    assert trace_id == "trace-manual-feed"

    with pytest.raises(PublicFeedRuntimeError) as missing:
        service.capture_once(feed_code="test.missing_feed.v1")
    assert missing.value.code == "PUBLIC_FEED_DEFINITION_NOT_FOUND"
    assert len(recording.calls) == 1


def test_bundle_rejects_empty_definitions() -> None:
    evidence = InMemoryRawSourceEvidenceStore()
    with pytest.raises(ValueError, match="at least one"):
        build_public_feed_runtime_bundle(
            definitions=(),
            adapter_factory=EvidenceBackedPublicHttpCaptureAdapterFactory(
                transport=FakeTransport(),  # type: ignore[arg-type]
                evidence_store=evidence,
            ),
            knowledge=InMemoryKnowledgeRepository(),
            evidence=evidence,
        )


def test_full_manual_capture_and_ingestion_worker_vertical_path() -> None:
    definition = _definition()
    evidence = InMemoryRawSourceEvidenceStore()
    knowledge = InMemoryKnowledgeRepository()
    ingestion_repository = InMemoryIngestionOrchestrationRepository()
    ingestion_service = IngestionOrchestrationService(ingestion_repository)
    transport = FakeTransport()
    bundle = build_public_feed_runtime_bundle(
        definitions=(definition,),
        adapter_factory=EvidenceBackedPublicHttpCaptureAdapterFactory(
            transport=transport,  # type: ignore[arg-type]
            evidence_store=evidence,
        ),
        knowledge=knowledge,
        evidence=evidence,
    )

    adoption = bundle.adoption_registry.get(definition.adapter_code)
    assert adoption.allowed_origins == (definition.origin,)
    assert bundle.capture_registry.get(definition.adapter_code).adapter_code == (
        definition.adapter_code
    )

    admission_repository = InMemorySourceProviderAdmissionRepository()
    admission = SourceProviderAdmissionService(
        admission_repository,
        clock=lambda: AT,
    )
    admission_repository.create_or_get(
        bundle.capability_templates[0].instantiate(created_at=AT)
    )
    public_executor = PermitBoundPublicCaptureExecutor(
        contexts=admission_repository,
        adapters=bundle.capture_registry,
    )
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=ingestion_service,
        registry=InMemorySourceCaptureRegistry(),
        observer=NoOpSourceAcquisitionObserver(),
        admission=admission,
        capture_executor=public_executor,
        clock=lambda: AT,
    )
    manual = ManualPublicFeedCaptureService(
        definitions=bundle.definitions,
        acquisition=acquisition,
    )

    capture = manual.capture_once(
        feed_code=definition.feed_code,
        trace_id="trace-public-feed",
    )

    assert capture.outcome is SourceAcquisitionOutcome.ADMITTED
    assert capture.source_artifact_id is not None
    assert capture.ingestion_run_id is not None
    assert len(transport.requests) == 1
    assert transport.requests[0].url == definition.external_locator
    artifact = knowledge.get_source_artifact(capture.source_artifact_id)
    assert artifact is not None
    assert artifact.raw_storage_ref is not None
    assert evidence.object_count == 1

    lease_repository = InMemoryIngestionRunLeaseRepository(ingestion_repository)
    worker = IngestionWorkerRunner(
        repository=ingestion_repository,
        orchestration=ingestion_service,
        leases=IngestionRunLeaseService(lease_repository),
        registry=bundle.ingestion_registry,
        observer=NoOpIngestionWorkerObserver(),
        clock=lambda: AT,
    )
    worker_result = worker.run_once(
        worker_ref="feed-worker",
        pipeline_code=PIPELINE_CODE,
        pipeline_version=PIPELINE_VERSION,
        ttl_seconds=60,
        trace_id="trace-feed-worker",
    )

    assert worker_result.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    proposals = ingestion_repository.list_proposals(capture.ingestion_run_id)
    assert len(proposals) == 1
    assert proposals[0].proposal_kind == "FEED_ITEM"
    assert proposals[0].payload["item_id"] == "item-001"
    assert proposals[0].risk_code == "UNREVIEWED_EXTERNAL_FEED_ITEM"
    assert ingestion_repository.get_review_decision(proposals[0].id) is None
    assert ingestion_repository.find_materialization(proposals[0].id) is None
