from __future__ import annotations

from collections import deque
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.infrastructure.canonical_public_feed_runtime import (
    CanonicalPublicFeedRuntimeProfileRegistry,
    MutableProviderAdoptionRegistry,
    MutablePublicSourceCaptureRegistry,
)
from kefe_api.modules.admin_security.models import AdminPrincipal, AdminRole
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PIPELINE_CODE,
    PIPELINE_VERSION,
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
from kefe_api.modules.knowledge.canonical_public_feed_catalog import (
    CanonicalPublicFeedCatalogService,
    InMemoryPublicFeedCatalogRepository,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
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
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile
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

NOW = datetime(2026, 8, 4, 15, 0, tzinfo=UTC)
ADAPTER_CODE = "kefe.public_feed.vertical.v1"
FEED_CODE = "vertical-feed"
FEED_URL = "https://feeds.example.test/vertical.xml"

RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Canonical Vertical Feed</title>
    <link>https://www.example.test/news</link>
    <description>Canonical feed snapshot</description>
    <lastBuildDate>Tue, 04 Aug 2026 14:50:00 GMT</lastBuildDate>
    <item>
      <guid>canonical-item-1</guid>
      <title>Canonical first item</title>
      <link>https://www.example.test/news/canonical-first</link>
      <pubDate>Tue, 04 Aug 2026 14:45:00 GMT</pubDate>
      <description>Canonical first summary</description>
    </item>
  </channel>
</rss>
"""


class _UnusedSessionResolver:
    def resolve(self, session_token: str):  # pragma: no cover
        raise AssertionError(session_token)

    def mark_seen(self, session_id, *, seen_at):  # pragma: no cover
        return None


class _FakeDnsResolver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def resolve(self, host: str) -> tuple[str, ...]:
        self.calls.append(host)
        return ("8.8.8.8",)


class _FakeBackend:
    def __init__(self, outcomes) -> None:
        self.outcomes = deque(outcomes)
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        outcome = self.outcomes.popleft()
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def _principal(role: AdminRole) -> AdminPrincipal:
    return AdminPrincipal(
        admin_subject_id=uuid4(),
        session_id=uuid4(),
        roles=frozenset({role}),
        direct_capabilities=frozenset(),
        authenticated_at=NOW - timedelta(minutes=5),
        mfa_satisfied_at=NOW - timedelta(minutes=5),
        step_up_at=NOW - timedelta(minutes=1),
        expires_at=NOW + timedelta(hours=2),
        last_seen_at=NOW - timedelta(minutes=1),
    )


def _definition() -> PublicFeedDefinition:
    return PublicFeedDefinition(
        feed_code=FEED_CODE,
        display_name="Canonical Vertical Feed",
        adapter_code=ADAPTER_CODE,
        external_locator=FEED_URL,
        parser_profile=StrictRssAtomParseProfile(),
        connect_timeout_ms=500,
        read_timeout_ms=1500,
        total_timeout_ms=2500,
        max_response_bytes=1_048_576,
        max_redirect_hops=1,
        terms_evidence_ref="evidence://provider-terms/vertical/v1",
        rate_limit_evidence_ref="evidence://provider-rate/vertical/v1",
        quota_limit=20,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=30,
        permit_ttl_seconds=30,
        language_code="tr",
        jurisdiction_code="TR",
    )


def _raw_response() -> RawHttpResponse:
    return RawHttpResponse(
        status_code=200,
        headers=(("content-type", "application/rss+xml; charset=utf-8"),),
        body=RSS_BODY,
        elapsed_ms=10,
    )


def test_approved_catalog_version_reaches_review_required_feed_item_proposal() -> None:
    knowledge = InMemoryKnowledgeRepository()
    evidence = InMemoryRawSourceEvidenceStore()
    provider_repository = InMemorySourceProviderAdmissionRepository()
    provider_service = SourceProviderAdmissionService(
        provider_repository,
        clock=lambda: NOW,
    )
    adoption = MutableProviderAdoptionRegistry()
    public_capture = MutablePublicSourceCaptureRegistry()
    resolver = _FakeDnsResolver()
    backend = _FakeBackend((_raw_response(),))
    transport = ControlledProviderHttpTransport(
        adoption_registry=adoption,
        dns_resolver=resolver,
        backend=backend,
        observer=NoOpProviderHttpObserver(),
        monotonic_clock=lambda: 0,
    )
    adapter_factory = EvidenceBackedPublicHttpCaptureAdapterFactory(
        transport=transport,
        evidence_store=evidence,
    )
    runtime_profiles = CanonicalPublicFeedRuntimeProfileRegistry(
        adoption=adoption,
        capture=public_capture,
        adapter_factory=adapter_factory,
    )
    public_executor = PermitBoundPublicCaptureExecutor(
        contexts=provider_repository,
        adapters=public_capture,
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
    security = AdminSecurityService(
        session_resolver=_UnusedSessionResolver(),
        policy=default_admin_security_policy(),
    )
    catalog_repository = InMemoryPublicFeedCatalogRepository()
    catalog = CanonicalPublicFeedCatalogService(
        repository=catalog_repository,
        security=security,
        provider_admission=provider_service,
        runtime_profiles=runtime_profiles,
        scheduler=scheduler,
        clock=lambda: NOW,
    )

    creator = _principal(AdminRole.REVIEWER)
    approver = _principal(AdminRole.REVIEWER)
    activator = _principal(AdminRole.ACCESS_ADMIN)
    draft = catalog.register_draft(
        creator,
        definition_version=1,
        definition=_definition(),
        interval_seconds=300,
        max_dispatch_attempts=3,
    )
    catalog.preflight(
        creator,
        feed_code=FEED_CODE,
        definition_version=1,
    )
    approved = catalog.approve(
        approver,
        feed_code=FEED_CODE,
        definition_version=1,
        expected_configuration_hash=draft.configuration_hash,
    )
    activation = catalog.activate(
        activator,
        feed_code=FEED_CODE,
        definition_version=1,
        expected_configuration_hash=approved.configuration_hash,
        first_due_at=NOW,
    )

    assert activation.adapter_code == ADAPTER_CODE
    assert resolver.calls == []
    assert backend.requests == []
    assert evidence.object_count == 0
    assert runtime_profiles.adapter_codes() == (ADAPTER_CODE,)

    dispatch = scheduler.plan_due_once(now=NOW)
    assert dispatch is not None
    execution = scheduler.execute_pending_once(
        worker_ref="canonical-source-worker",
        ttl_seconds=30,
        trace_id="trace-canonical-source",
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
    assert run.configuration_hash == _definition().configuration_hash

    worker_registry = build_feed_item_extraction_runtime(
        FeedItemExtractionStageProcessor(
            knowledge=knowledge,
            evidence=evidence,
        )
    )
    worker = IngestionWorkerRunner(
        repository=ingestion_repository,
        orchestration=ingestion_service,
        leases=IngestionRunLeaseService(
            InMemoryIngestionRunLeaseRepository(ingestion_repository)
        ),
        registry=worker_registry,
        observer=NoOpIngestionWorkerObserver(),
        clock=lambda: NOW,
        monotonic_clock=lambda: 0,
    )
    result = worker.run_once(
        worker_ref="canonical-feed-item-worker",
        pipeline_code=PIPELINE_CODE,
        pipeline_version=PIPELINE_VERSION,
        ttl_seconds=30,
        trace_id="trace-canonical-feed-items",
    )

    assert result.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    proposals = ingestion_repository.list_proposals(run.id)
    assert len(proposals) == 1
    assert proposals[0].proposal_kind == "FEED_ITEM"
    assert proposals[0].payload["item_id"] == "canonical-item-1"
    assert ingestion_repository.get_review_decision(proposals[0].id) is None
    assert ingestion_repository.find_materialization(proposals[0].id) is None
    assert catalog_repository.list_audit(draft.id)[-1].action.value == "ACTIVATED"
