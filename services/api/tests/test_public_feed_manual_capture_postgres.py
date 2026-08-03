from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from kefe_api.infrastructure.postgres_public_feed_catalog import (
    PostgresPublicFeedCatalogRepository,
)
from kefe_api.infrastructure.postgres_public_feed_manual_capture import (
    PostgresPublicFeedManualCaptureAuditRepository,
)
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminPrincipal, AdminRole
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.knowledge.public_feed_catalog import PublicFeedCatalogService
from kefe_api.modules.knowledge.public_feed_manual_capture import (
    ApprovedPublicFeedManualCaptureService,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile
from kefe_api.modules.knowledge.source_acquisition import (
    SourceAcquisitionOutcome,
    SourceAcquisitionResult,
)

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _definition(suffix: str) -> PublicFeedDefinition:
    return PublicFeedDefinition(
        feed_code=f"test.pg_manual_feed_{suffix}.v1",
        display_name="PostgreSQL Manual Feed",
        adapter_code=f"test.pg_manual_rss_{suffix}.v1",
        external_locator=f"https://manual-{suffix}.example.test/feed.xml",
        parser_profile=StrictRssAtomParseProfile(),
        connect_timeout_ms=1000,
        read_timeout_ms=1500,
        total_timeout_ms=3000,
        max_response_bytes=1_048_576,
        max_redirect_hops=1,
        terms_evidence_ref=f"evidence://terms/manual-{suffix}",
        rate_limit_evidence_ref=f"evidence://rate/manual-{suffix}",
        quota_limit=20,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=120,
        permit_ttl_seconds=30,
        language_code="en",
        jurisdiction_code="GLOBAL",
    )


def _principal(at: datetime) -> AdminPrincipal:
    return AdminPrincipal(
        admin_subject_id=uuid4(),
        session_id=uuid4(),
        roles=frozenset({AdminRole.REVIEWER}),
        direct_capabilities=frozenset(),
        authenticated_at=at - timedelta(minutes=5),
        mfa_satisfied_at=at - timedelta(minutes=5),
        step_up_at=at,
        expires_at=at + timedelta(hours=8),
        last_seen_at=at,
    )


def _security() -> AdminSecurityService:
    return AdminSecurityService(
        session_resolver=InMemoryAdminSessionStore(),
        policy=default_admin_security_policy(),
    )


class RecordingRuntime:
    def __init__(self) -> None:
        self.calls = []

    def execute(self, *, definition, trace_id, at):
        self.calls.append((definition, trace_id, at))
        command = definition.acquisition_command()
        return SourceAcquisitionResult(
            outcome=SourceAcquisitionOutcome.BLOCKED,
            adapter_code=definition.adapter_code,
            pipeline_code=command.pipeline_code,
            pipeline_version=command.pipeline_version,
            trace_id=trace_id,
            duration_ms=9,
            error_code="TEST_POSTGRES_BLOCKED",
        )


def test_postgres_manual_capture_audit_survives_restart() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    at = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid4().hex[:10]
    principal = _principal(at)
    security = _security()
    catalog_repository = PostgresPublicFeedCatalogRepository(engine)
    catalog_service = PublicFeedCatalogService(
        repository=catalog_repository,
        security=security,
        clock=lambda: at,
    )
    registered = catalog_service.register(principal, _definition(suffix))
    approved = catalog_service.approve_manual_capture(principal, registered.id)
    runtime = RecordingRuntime()
    audit_repository = PostgresPublicFeedManualCaptureAuditRepository(engine)
    service = ApprovedPublicFeedManualCaptureService(
        catalog=catalog_repository,
        runtime=runtime,
        audit=audit_repository,
        security=security,
        clock=lambda: at,
    )

    result = service.capture_once(
        principal,
        catalog_entry_id=approved.id,
        trace_id=f"trace-pg-{suffix}",
    )

    restarted = PostgresPublicFeedManualCaptureAuditRepository(engine)
    events = restarted.list_entries(approved.id)
    assert result.outcome is SourceAcquisitionOutcome.BLOCKED
    assert len(runtime.calls) == 1
    assert [item.outcome for item in events] == [
        "ATTEMPT_STARTED",
        "BLOCKED",
    ]
    assert events[0].execution_id == events[1].execution_id == result.execution_id
    assert events[1].error_code == "TEST_POSTGRES_BLOCKED"
    assert events[0].actor_ref == principal.audit_actor_ref


def test_postgres_manual_capture_audit_is_append_only() -> None:
    engine = create_engine(os.environ["KEFE_DATABASE_URL"])
    at = datetime.now(UTC).replace(microsecond=0)
    suffix = uuid4().hex[:10]
    principal = _principal(at)
    security = _security()
    catalog_repository = PostgresPublicFeedCatalogRepository(engine)
    catalog_service = PublicFeedCatalogService(
        repository=catalog_repository,
        security=security,
        clock=lambda: at,
    )
    registered = catalog_service.register(principal, _definition(suffix))
    approved = catalog_service.approve_manual_capture(principal, registered.id)
    audit_repository = PostgresPublicFeedManualCaptureAuditRepository(engine)
    service = ApprovedPublicFeedManualCaptureService(
        catalog=catalog_repository,
        runtime=RecordingRuntime(),
        audit=audit_repository,
        security=security,
        clock=lambda: at,
    )
    result = service.capture_once(
        principal,
        catalog_entry_id=approved.id,
        trace_id=f"trace-append-{suffix}",
    )
    events = audit_repository.list_entries(approved.id)
    assert len(events) == 2

    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE knowledge.public_feed_manual_capture_audit
                    SET error_code = 'FORGED'
                    WHERE event_id = :event_id
                    """
                ),
                {"event_id": events[-1].event_id},
            )
    with pytest.raises(DBAPIError):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM knowledge.public_feed_manual_capture_audit
                    WHERE event_id = :event_id
                    """
                ),
                {"event_id": events[0].event_id},
            )

    preserved = PostgresPublicFeedManualCaptureAuditRepository(engine).list_entries(
        approved.id
    )
    assert [item.event_id for item in preserved] == [
        events[0].event_id,
        events[1].event_id,
    ]
    assert preserved[-1].execution_id == result.execution_id
