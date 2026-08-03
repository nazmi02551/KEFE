from __future__ import annotations

import re
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
    InMemoryIngestionWorkerObserver,
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
from kefe_api.modules.knowledge.provider_http_transport import ProviderHttpResponse
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
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile
from kefe_api.modules.knowledge.rss_atom_route import (
    InMemoryRssAtomRouteRegistry,
    RssAtomRouteFactory,
    RssAtomRouteProfile,
)
from kefe_api.modules.knowledge.source_acquisition import (
    InMemorySourceCaptureRegistry,
    NoOpSourceAcquisitionObserver,
    SourceAcquisitionOutcome,
    SourceAcquisitionService,
)
from kefe_api.modules.knowledge.source_evidence import (
    InMemoryRawSourceEvidenceStore,
    canonical_content_hash,
)

NOW = datetime(2026, 8, 3, 9, 0, tzinfo=UTC)
ROUTE_CODE = "test.rss_atom_route.v1"
ADAPTER_CODE = "test.rss_atom_feed.v1"
FEED_URL = "https://feeds.example.test/news.xml"

RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example Route Feed</title>
    <link>https://www.example.test/news</link>
    <description>Route feed snapshot</description>
    <lastBuildDate>Mon, 03 Aug 2026 08:50:00 GMT</lastBuildDate>
    <item>
      <guid>item-b</guid>
      <title>Second route item</title>
      <link>https://www.example.test/news/b</link>
      <pubDate>Mon, 03 Aug 2026 08:42:00 GMT</pubDate>
      <description>Second route summary.</description>
    </item>
    <item>
      <guid>item-a</guid>
      <title>First route item</title>
      <link>https://www.example.test/news/a</link>
      <pubDate>Mon, 03 Aug 2026 08:41:00 GMT</pubDate>
      <description>First route summary.</description>
    </item>
  </channel>
</rss>
"""


class StaticPublicTransport:
    def __init__(self, response: ProviderHttpResponse) -> None:
        self.response = response
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return self.response


def _response() -> ProviderHttpResponse:
    return ProviderHttpResponse(
        status_code=200,
        media_type="application/rss+xml",
        body=RSS_BODY,
        redirect_hops=0,
        elapsed_ms=7,
    )


def _profile(**overrides) -> RssAtomRouteProfile:
    values = {
        "route_code": ROUTE_CODE,
        "adapter_code": ADAPTER_CODE,
        "parser_profile": StrictRssAtomParseProfile(),
        "locale": "tr-TR",
        "jurisdiction_code": "TR",
    }
    values.update(overrides)
    return RssAtomRouteProfile(**values)


def _factory(
    *,
    transport: StaticPublicTransport | None = None,
    evidence: InMemoryRawSourceEvidenceStore | None = None,
    knowledge: InMemoryKnowledgeRepository | None = None,
):
    resolved_transport = transport or StaticPublicTransport(_response())
    resolved_evidence = evidence or InMemoryRawSourceEvidenceStore()
    resolved_knowledge = knowledge or InMemoryKnowledgeRepository()
    factory = RssAtomRouteFactory(
        transport=resolved_transport,  # type: ignore[arg-type]
        evidence_store=resolved_evidence,
        knowledge_repository=resolved_knowledge,
    )
    return factory, resolved_transport, resolved_evidence, resolved_knowledge


def test_route_profile_derives_exact_configuration_and_command() -> None:
    parser_profile = StrictRssAtomParseProfile(max_items=32)
    profile = _profile(parser_profile=parser_profile)

    assert profile.parser_profile is parser_profile
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", profile.configuration_hash)
    assert profile.configuration_hash == profile.configuration_hash
    assert _profile(parser_profile=parser_profile).configuration_hash == (
        profile.configuration_hash
    )
    assert _profile(
        parser_profile=StrictRssAtomParseProfile(max_items=31)
    ).configuration_hash != profile.configuration_hash

    command = profile.acquisition_command(FEED_URL)
    assert command.adapter_code == ADAPTER_CODE
    assert command.pipeline_code == "RSS_ATOM_FEED_ITEM_EXTRACTION"
    assert command.pipeline_version == "1.0.0"
    assert command.configuration_hash == profile.configuration_hash
    assert command.locale == "tr-TR"
    assert command.jurisdiction_code == "TR"

    with pytest.raises(ValueError):
        profile.acquisition_command(" https://feeds.example.test/news.xml")


def test_factory_pins_one_profile_store_adapter_processor_and_registry() -> None:
    factory, _, evidence, _ = _factory()
    profile = _profile()
    route = factory.build(profile)

    assert route.profile is profile
    assert route.capture_definition.profile is profile.parser_profile
    assert route.capture_definition.adapter_code == ADAPTER_CODE
    assert route.public_adapter.adapter_code == ADAPTER_CODE
    assert getattr(route.extraction_processor, "_profile") is profile.parser_profile
    assert getattr(route.extraction_processor, "_evidence") is evidence
    assert route.ingestion_registry.get_processor(
        pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
        pipeline_version="1.0.0",
        stage_code="EXTRACT_FEED_ITEMS",
        stage_version="1.0.0",
    ) is route.extraction_processor

    registry = InMemoryRssAtomRouteRegistry((route,))
    assert registry.route_count == 1
    assert registry.get(ROUTE_CODE) is route
    assert registry.get_by_adapter_code(ADAPTER_CODE) is route
    with pytest.raises(KeyError):
        registry.get("test.missing_route.v1")
    with pytest.raises(ValueError, match="duplicate RSS/Atom route code"):
        InMemoryRssAtomRouteRegistry((route, route))

    second = factory.build(
        _profile(route_code="test.second_route.v1")
    )
    with pytest.raises(ValueError, match="duplicate RSS/Atom route adapter code"):
        InMemoryRssAtomRouteRegistry((route, second))


def test_route_factory_requires_one_readable_and_writable_evidence_store() -> None:
    class SealOnlyStore:
        def seal(self, **kwargs):
            del kwargs
            raise AssertionError

    with pytest.raises(ValueError, match="seal and read"):
        RssAtomRouteFactory(
            transport=StaticPublicTransport(_response()),  # type: ignore[arg-type]
            evidence_store=SealOnlyStore(),  # type: ignore[arg-type]
            knowledge_repository=InMemoryKnowledgeRepository(),
        )


def test_full_public_route_reaches_review_required_feed_item_proposals() -> None:
    transport = StaticPublicTransport(_response())
    evidence = InMemoryRawSourceEvidenceStore()
    knowledge = InMemoryKnowledgeRepository()
    factory, _, _, _ = _factory(
        transport=transport,
        evidence=evidence,
        knowledge=knowledge,
    )
    route = factory.build(_profile())

    provider_repository = InMemorySourceProviderAdmissionRepository()
    provider = SourceProviderAdmissionService(
        provider_repository,
        clock=lambda: NOW,
    )
    provider.register(
        adapter_code=route.adapter_code,
        credential_mode=ProviderCredentialMode.PUBLIC,
        secret_ref=None,
        quota_limit=10,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=30,
        permit_ttl_seconds=30,
        created_at=NOW,
    )
    public_executor = PermitBoundPublicCaptureExecutor(
        contexts=provider_repository,
        adapters=InMemoryPublicSourceCaptureRegistry((route.public_adapter,)),
    )
    secure_executor = SecureProviderCaptureExecutor(
        contexts=provider_repository,
        resolvers=InMemorySecretResolverRegistry(),
        adapters=InMemoryCredentialAwareSourceCaptureRegistry(),
    )
    capture_router = CredentialModeRoutingProviderCaptureExecutor(
        contexts=provider_repository,
        public_executor=public_executor,
        credentialed_executor=secure_executor,
    )

    ingestion_repository = InMemoryIngestionOrchestrationRepository()
    ingestion = IngestionOrchestrationService(ingestion_repository)
    acquisition = SourceAcquisitionService(
        knowledge_repository=knowledge,
        ingestion_service=ingestion,
        registry=InMemorySourceCaptureRegistry(),
        observer=NoOpSourceAcquisitionObserver(),
        admission=provider,
        capture_executor=capture_router,
        clock=lambda: NOW,
    )

    acquired = acquisition.acquire(
        route.acquisition_command(FEED_URL),
        trace_id="trace-route-vertical",
    )

    assert acquired.outcome is SourceAcquisitionOutcome.ADMITTED
    assert transport.requests
    assert evidence.object_count == 1
    artifact = knowledge.get_source_artifact(acquired.source_artifact_id)
    assert artifact is not None
    assert artifact.content_hash == canonical_content_hash(RSS_BODY)
    assert artifact.raw_storage_ref is not None
    run = ingestion_repository.get_run(acquired.ingestion_run_id)
    assert run is not None
    assert run.configuration_hash == route.profile.configuration_hash
    assert run.pipeline_code == "RSS_ATOM_FEED_ITEM_EXTRACTION"

    lease_repository = InMemoryIngestionRunLeaseRepository(ingestion_repository)
    observer = InMemoryIngestionWorkerObserver()
    runner = IngestionWorkerRunner(
        repository=ingestion_repository,
        orchestration=ingestion,
        leases=IngestionRunLeaseService(lease_repository),
        registry=route.ingestion_registry,
        observer=observer,
        clock=lambda: NOW,
    )
    result = runner.run_once(
        worker_ref="worker-rss-route",
        pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
        pipeline_version="1.0.0",
        ttl_seconds=60,
        trace_id="trace-route-worker",
    )

    assert result.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    assert ingestion_repository.get_run(run.id).state is IngestionRunState.SUCCEEDED
    proposals = ingestion_repository.list_proposals(run.id)
    assert [proposal.payload["item_id"] for proposal in proposals] == [
        "item-a",
        "item-b",
    ]
    assert all(proposal.proposal_kind == "FEED_ITEM" for proposal in proposals)
    assert all(
        ingestion_repository.get_review_decision(proposal.id) is None
        for proposal in proposals
    )
    assert all(
        ingestion_repository.find_materialization(proposal.id) is None
        for proposal in proposals
    )
    permit = next(iter(provider_repository._permits.values()))
    assert permit.state.value == "SUCCEEDED"
