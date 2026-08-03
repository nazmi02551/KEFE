from __future__ import annotations

from dataclasses import replace
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
from kefe_api.modules.knowledge.rss_atom_route_scheduling import (
    RssAtomRouteScheduleError,
    RssAtomRouteScheduleRequest,
    RssAtomRouteScheduleService,
)
from kefe_api.modules.knowledge.source_acquisition import (
    InMemorySourceCaptureRegistry,
    NoOpSourceAcquisitionObserver,
    SourceAcquisitionService,
)
from kefe_api.modules.knowledge.source_evidence import InMemoryRawSourceEvidenceStore
from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionScheduleState,
    build_source_schedule_key,
)
from kefe_api.modules.knowledge.source_scheduler_memory import (
    InMemorySourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    InMemorySourceDispatchObserver,
    SourceAcquisitionSchedulerService,
    SourceDispatchExecutionOutcome,
)

NOW = datetime(2026, 8, 3, 10, 0, tzinfo=UTC)
ROUTE_CODE = "test.scheduled_rss_route.v1"
ADAPTER_CODE = "test.scheduled_rss_feed.v1"
FEED_URL = "https://feeds.example.test/scheduled.xml"

RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Scheduled Example Feed</title>
    <link>https://www.example.test/scheduled</link>
    <description>Scheduled snapshot</description>
    <lastBuildDate>Mon, 03 Aug 2026 09:55:00 GMT</lastBuildDate>
    <item>
      <guid>scheduled-item-1</guid>
      <title>Scheduled route item</title>
      <link>https://www.example.test/scheduled/1</link>
      <pubDate>Mon, 03 Aug 2026 09:50:00 GMT</pubDate>
      <description>Scheduled route summary.</description>
    </item>
  </channel>
</rss>
"""


class StaticPublicTransport:
    def __init__(self) -> None:
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return ProviderHttpResponse(
            status_code=200,
            media_type="application/rss+xml",
            body=RSS_BODY,
            redirect_hops=0,
            elapsed_ms=5,
        )


def _route_runtime():
    transport = StaticPublicTransport()
    evidence = InMemoryRawSourceEvidenceStore()
    knowledge = InMemoryKnowledgeRepository()
    profile = RssAtomRouteProfile(
        route_code=ROUTE_CODE,
        adapter_code=ADAPTER_CODE,
        parser_profile=StrictRssAtomParseProfile(max_items=32),
        locale="tr-TR",
        jurisdiction_code="TR",
    )
    route = RssAtomRouteFactory(
        transport=transport,  # type: ignore[arg-type]
        evidence_store=evidence,
        knowledge_repository=knowledge,
    ).build(profile)
    return route, transport, evidence, knowledge


def _generic_scheduler(*, acquisition, repository=None):
    resolved_repository = repository or InMemorySourceAcquisitionSchedulerRepository()
    scheduler = SourceAcquisitionSchedulerService(
        repository=resolved_repository,
        acquisition=acquisition,
        observer=InMemorySourceDispatchObserver(),
        clock=lambda: NOW,
    )
    return resolved_repository, scheduler


def _request() -> RssAtomRouteScheduleRequest:
    return RssAtomRouteScheduleRequest(
        route_code=ROUTE_CODE,
        external_locator=FEED_URL,
        first_due_at=NOW,
        interval_seconds=300,
        max_dispatch_attempts=3,
    )


def test_route_schedule_derives_exact_command_key_and_is_idempotent() -> None:
    route, _, _, _ = _route_runtime()
    repository, scheduler = _generic_scheduler(acquisition=object())
    service = RssAtomRouteScheduleService(
        routes=InMemoryRssAtomRouteRegistry((route,)),
        scheduler=scheduler,
    )

    first = service.create(_request(), now=NOW)
    second = service.create(_request(), now=NOW)
    command = route.acquisition_command(FEED_URL)
    expected_key = build_source_schedule_key(
        adapter_code=command.adapter_code,
        external_locator=command.external_locator,
        pipeline_code=command.pipeline_code,
        pipeline_version=command.pipeline_version,
        configuration_hash=command.configuration_hash,
        first_due_at=NOW,
        interval_seconds=300,
        max_dispatch_attempts=3,
        taxonomy_version=command.taxonomy_version,
        methodology_version=command.methodology_version,
        locale=command.locale,
        jurisdiction_code=command.jurisdiction_code,
    )

    assert first.id == second.id
    assert first.schedule_key == expected_key
    assert first.adapter_code == ADAPTER_CODE
    assert first.pipeline_code == "RSS_ATOM_FEED_ITEM_EXTRACTION"
    assert first.pipeline_version == "1.0.0"
    assert first.configuration_hash == route.profile.configuration_hash
    assert first.locale == "tr-TR"
    assert first.jurisdiction_code == "TR"
    assert repository.get_schedule(first.id) == first
    assert service.reconcile(first) is route


def test_route_schedule_missing_route_and_command_drift_fail_closed() -> None:
    route, _, _, _ = _route_runtime()
    _, scheduler = _generic_scheduler(acquisition=object())
    missing = RssAtomRouteScheduleService(
        routes=InMemoryRssAtomRouteRegistry(),
        scheduler=scheduler,
    )
    with pytest.raises(RssAtomRouteScheduleError) as missing_route:
        missing.create(_request(), now=NOW)
    assert missing_route.value.code == (
        "RSS_ATOM_ROUTE_SCHEDULE_ROUTE_NOT_REGISTERED"
    )

    service = RssAtomRouteScheduleService(
        routes=InMemoryRssAtomRouteRegistry((route,)),
        scheduler=scheduler,
    )
    schedule = service.create(_request(), now=NOW)
    for drifted in (
        replace(schedule, pipeline_version="2.0.0"),
        replace(schedule, configuration_hash="sha256:route-drift"),
        replace(schedule, locale="en-US"),
    ):
        with pytest.raises(RssAtomRouteScheduleError) as drift:
            service.reconcile(drifted)
        assert drift.value.code == "RSS_ATOM_ROUTE_SCHEDULE_DRIFT"


def test_generic_scheduler_retains_route_schedule_lifecycle_authority() -> None:
    route, _, _, _ = _route_runtime()
    _, scheduler = _generic_scheduler(acquisition=object())
    service = RssAtomRouteScheduleService(
        routes=InMemoryRssAtomRouteRegistry((route,)),
        scheduler=scheduler,
    )
    schedule = service.create(_request(), now=NOW)

    paused = scheduler.pause(schedule.id, now=NOW)
    resumed = scheduler.resume(schedule.id, now=NOW)
    retired = scheduler.retire(schedule.id, now=NOW)

    assert paused.state is SourceAcquisitionScheduleState.PAUSED
    assert resumed.state is SourceAcquisitionScheduleState.ACTIVE
    assert retired.state is SourceAcquisitionScheduleState.RETIRED


def test_scheduled_route_dispatch_reaches_review_required_feed_item_proposals() -> None:
    route, transport, evidence, knowledge = _route_runtime()
    provider_repository = InMemorySourceProviderAdmissionRepository()
    provider = SourceProviderAdmissionService(
        provider_repository,
        clock=lambda: NOW,
    )
    provider.register(
        adapter_code=ADAPTER_CODE,
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
    capture_router = CredentialModeRoutingProviderCaptureExecutor(
        contexts=provider_repository,
        public_executor=public_executor,
        credentialed_executor=SecureProviderCaptureExecutor(
            contexts=provider_repository,
            resolvers=InMemorySecretResolverRegistry(),
            adapters=InMemoryCredentialAwareSourceCaptureRegistry(),
        ),
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
    scheduler_repository, scheduler = _generic_scheduler(acquisition=acquisition)
    service = RssAtomRouteScheduleService(
        routes=InMemoryRssAtomRouteRegistry((route,)),
        scheduler=scheduler,
    )
    schedule = service.create(_request(), now=NOW)

    dispatch = scheduler.plan_due_once(now=NOW)
    executed = scheduler.execute_pending_once(
        worker_ref="route-dispatch-worker",
        ttl_seconds=60,
        trace_id="trace-route-schedule-dispatch",
        now=NOW,
    )

    assert dispatch is not None
    assert executed.outcome is SourceDispatchExecutionOutcome.SUCCEEDED
    assert executed.source_artifact_id is not None
    assert executed.ingestion_run_id is not None
    assert transport.requests
    assert evidence.object_count == 1
    assert scheduler_repository.get_schedule(schedule.id).next_due_at == (
        NOW.replace(minute=5)
    )

    runner = IngestionWorkerRunner(
        repository=ingestion_repository,
        orchestration=ingestion,
        leases=IngestionRunLeaseService(
            InMemoryIngestionRunLeaseRepository(ingestion_repository)
        ),
        registry=route.ingestion_registry,
        observer=InMemoryIngestionWorkerObserver(),
        clock=lambda: NOW,
    )
    worker_result = runner.run_once(
        worker_ref="route-ingestion-worker",
        pipeline_code="RSS_ATOM_FEED_ITEM_EXTRACTION",
        pipeline_version="1.0.0",
        ttl_seconds=60,
        trace_id="trace-route-schedule-worker",
    )

    assert worker_result.outcome is IngestionWorkerRunOutcome.SUCCEEDED
    run = ingestion_repository.get_run(executed.ingestion_run_id)
    assert run is not None and run.state is IngestionRunState.SUCCEEDED
    proposals = ingestion_repository.list_proposals(run.id)
    assert len(proposals) == 1
    assert proposals[0].proposal_kind == "FEED_ITEM"
    assert proposals[0].payload["item_id"] == "scheduled-item-1"
    assert ingestion_repository.get_review_decision(proposals[0].id) is None
    assert ingestion_repository.find_materialization(proposals[0].id) is None
