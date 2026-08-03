from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, text

from kefe_api.infrastructure.postgres_source_acquisition_scheduler import (
    PostgresSourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.knowledge.in_memory import InMemoryKnowledgeRepository
from kefe_api.modules.knowledge.provider_http_transport import ProviderHttpResponse
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile
from kefe_api.modules.knowledge.rss_atom_route import (
    InMemoryRssAtomRouteRegistry,
    RssAtomRouteFactory,
    RssAtomRouteProfile,
)
from kefe_api.modules.knowledge.rss_atom_route_scheduling import (
    RssAtomRouteScheduleRequest,
    RssAtomRouteScheduleService,
)
from kefe_api.modules.knowledge.source_evidence import InMemoryRawSourceEvidenceStore
from kefe_api.modules.knowledge.source_scheduler_service import (
    InMemorySourceDispatchObserver,
    SourceAcquisitionSchedulerService,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)

NOW = datetime(2026, 8, 3, 10, 30, tzinfo=UTC)
ROUTE_CODE = "test.pg_rss_route.v1"
ADAPTER_CODE = "test.pg_rss_feed.v1"
FEED_URL = "https://feeds.example.test/postgres.xml"


@pytest.fixture(autouse=True)
def _isolate_route_schedule_ledger():
    if os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1":
        yield
        return
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM knowledge.source_acquisition_dispatch"))
        connection.execute(text("DELETE FROM knowledge.source_acquisition_schedule"))
    yield


class UnusedTransport:
    def execute(self, request):
        del request
        return ProviderHttpResponse(
            status_code=200,
            media_type="application/rss+xml",
            body=b"<rss version='2.0'><channel><title>x</title></channel></rss>",
            redirect_hops=0,
            elapsed_ms=1,
        )


def test_postgres_route_schedule_create_is_idempotent_and_reconcilable() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    repository = PostgresSourceAcquisitionSchedulerRepository(engine)
    scheduler = SourceAcquisitionSchedulerService(
        repository=repository,
        acquisition=object(),
        observer=InMemorySourceDispatchObserver(),
        clock=lambda: NOW,
    )
    route = RssAtomRouteFactory(
        transport=UnusedTransport(),  # type: ignore[arg-type]
        evidence_store=InMemoryRawSourceEvidenceStore(),
        knowledge_repository=InMemoryKnowledgeRepository(),
    ).build(
        RssAtomRouteProfile(
            route_code=ROUTE_CODE,
            adapter_code=ADAPTER_CODE,
            parser_profile=StrictRssAtomParseProfile(max_items=16),
            locale="en",
            jurisdiction_code="ZZ",
        )
    )
    service = RssAtomRouteScheduleService(
        routes=InMemoryRssAtomRouteRegistry((route,)),
        scheduler=scheduler,
    )
    request = RssAtomRouteScheduleRequest(
        route_code=ROUTE_CODE,
        external_locator=FEED_URL,
        first_due_at=NOW,
        interval_seconds=600,
        max_dispatch_attempts=3,
    )

    first = service.create(request, now=NOW)
    second = service.create(request, now=NOW)
    stored = repository.get_schedule(first.id)

    assert first.id == second.id
    assert stored == first
    assert stored is not None
    assert stored.adapter_code == ADAPTER_CODE
    assert stored.pipeline_code == "RSS_ATOM_FEED_ITEM_EXTRACTION"
    assert stored.configuration_hash == route.profile.configuration_hash
    assert service.reconcile(stored) is route
