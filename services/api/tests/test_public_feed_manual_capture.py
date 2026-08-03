from __future__ import annotations

from collections import deque
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.infrastructure.provider_http_runtime import (
    ProviderHttpRuntimeComponents,
    ProviderHttpRuntimeMode,
)
from kefe_api.infrastructure.public_feed_manual_capture_runtime import (
    InvocationScopedPublicFeedManualCaptureRuntime,
)
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import AdminPrincipal, AdminRole
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.models import IngestionRunState
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
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
    InMemoryProviderHttpObserver,
    RawHttpResponse,
)
from kefe_api.modules.knowledge.public_feed_catalog import (
    InMemoryPublicFeedCatalogRepository,
    PublicFeedCatalogService,
    PublicFeedCatalogState,
)
from kefe_api.modules.knowledge.public_feed_manual_capture import (
    ApprovedPublicFeedManualCaptureService,
    InMemoryPublicFeedManualCaptureAuditRepository,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile
from kefe_api.modules.knowledge.source_acquisition import (
    NoOpSourceAcquisitionObserver,
    SourceAcquisitionOutcome,
    SourceAcquisitionResult,
)
from kefe_api.modules.knowledge.source_evidence import InMemoryRawSourceEvidenceStore

AT = datetime(2026, 8, 3, 18, 0, tzinfo=UTC)
RSS_BODY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Approved Feed</title>
    <link>https://approved.example.test/</link>
    <description>Approved feed description.</description>
    <language>en</language>
    <lastBuildDate>Mon, 03 Aug 2026 18:00:00 GMT</lastBuildDate>
    <item>
      <guid>approved-item-1</guid>
      <title>Approved item</title>
      <link>https://approved.example.test/items/1</link>
      <pubDate>Mon, 03 Aug 2026 17:30:00 GMT</pubDate>
      <description>Approved item summary.</description>
    </item>
  </channel>
</rss>
"""


def _definition() -> PublicFeedDefinition:
    return PublicFeedDefinition(
        feed_code="test.approved_feed.v1",
        display_name="Approved Feed",
        adapter_code="test.approved_rss.v1",
        external_locator="https://approved.example.test/feed.xml",
        parser_profile=StrictRssAtomParseProfile(),
        connect_timeout_ms=1000,
        read_timeout_ms=1500,
        total_timeout_ms=3000,
        max_response_bytes=1_048_576,
        max_redirect_hops=1,
        terms_evidence_ref="evidence://terms/approved-feed-v1",
        rate_limit_evidence_ref="evidence://rate/approved-feed-v1",
        quota_limit=20,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=120,
        permit_ttl_seconds=30,
        language_code="en",
        jurisdiction_code="GLOBAL",
    )


def _principal(*, step_up: bool = True) -> AdminPrincipal:
    return AdminPrincipal(
        admin_subject_id=uuid4(),
        session_id=uuid4(),
        roles=frozenset({AdminRole.REVIEWER}),
        direct_capabilities=frozenset(),
        authenticated_at=AT - timedelta(minutes=5),
        mfa_satisfied_at=AT - timedelta(minutes=5),
        step_up_at=AT if step_up else None,
        expires_at=AT + timedelta(hours=8),
        last_seen_at=AT,
    )


def _security() -> AdminSecurityService:
    return AdminSecurityService(
        session_resolver=InMemoryAdminSessionStore(),
        policy=default_admin_security_policy(),
    )


def _approved_catalog():
    repository = InMemoryPublicFeedCatalogRepository()
    security = _security()
    service = PublicFeedCatalogService(
        repository=repository,
        security=security,
        clock=lambda: AT,
    )
    principal = _principal()
    registered = service.register(principal, _definition())
    approved = service.approve_manual_capture(principal, registered.id)
    assert approved.state is PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED
    return repository, security, principal, approved


class RecordingRuntime:
    def __init__(self, result: SourceAcquisitionResult | BaseException) -> None:
        self.result = result
        self.calls = []

    def execute(self, *, definition, trace_id, at):
        self.calls.append((definition, trace_id, at))
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


class FailingAuditRepository(InMemoryPublicFeedManualCaptureAuditRepository):
    def append(self, entry):
        del entry
        raise RuntimeError("private audit backend details")


class FakeDnsResolver:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def resolve(self, host: str) -> tuple[str, ...]:
        self.calls.append(host)
        return ("8.8.8.8",)


class FakePinnedBackend:
    def __init__(self, responses) -> None:
        self.responses = deque(responses)
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        response = self.responses.popleft()
        if isinstance(response, BaseException):
            raise response
        return response


def _raw_rss_response() -> RawHttpResponse:
    return RawHttpResponse(
        status_code=200,
        headers=(("content-type", "application/rss+xml; charset=utf-8"),),
        body=RSS_BODY,
        elapsed_ms=14,
    )


def test_registered_retired_and_missing_entries_never_execute() -> None:
    catalog = InMemoryPublicFeedCatalogRepository()
    security = _security()
    principal = _principal()
    catalog_service = PublicFeedCatalogService(
        repository=catalog,
        security=security,
        clock=lambda: AT,
    )
    registered = catalog_service.register(principal, _definition())
    runtime = RecordingRuntime(RuntimeError("must not execute"))
    audit = InMemoryPublicFeedManualCaptureAuditRepository()
    service = ApprovedPublicFeedManualCaptureService(
        catalog=catalog,
        runtime=runtime,
        audit=audit,
        security=security,
        clock=lambda: AT,
    )

    with pytest.raises(DomainError) as not_approved:
        service.capture_once(principal, catalog_entry_id=registered.id)
    assert not_approved.value.code == "PUBLIC_FEED_MANUAL_CAPTURE_NOT_APPROVED"

    retired = catalog_service.retire(
        principal,
        registered.id,
        rationale="Registration retired before capture.",
    )
    assert retired.state is PublicFeedCatalogState.RETIRED
    with pytest.raises(DomainError) as retired_error:
        service.capture_once(principal, catalog_entry_id=retired.id)
    assert retired_error.value.code == "PUBLIC_FEED_MANUAL_CAPTURE_NOT_APPROVED"

    with pytest.raises(DomainError) as missing:
        service.capture_once(principal, catalog_entry_id=uuid4())
    assert missing.value.code == "PUBLIC_FEED_CATALOG_NOT_FOUND"
    assert runtime.calls == []
    assert audit.list_entries() == ()


def test_fresh_step_up_and_started_audit_are_required_before_runtime() -> None:
    catalog, security, _, approved = _approved_catalog()
    runtime = RecordingRuntime(
        SourceAcquisitionResult(
            outcome=SourceAcquisitionOutcome.BLOCKED,
            adapter_code=approved.adapter_code,
            pipeline_code=approved.definition.acquisition_command().pipeline_code,
            pipeline_version=approved.definition.acquisition_command().pipeline_version,
            trace_id="trace-step-up",
            duration_ms=0,
            error_code="TEST_BLOCKED",
        )
    )
    audit = InMemoryPublicFeedManualCaptureAuditRepository()
    service = ApprovedPublicFeedManualCaptureService(
        catalog=catalog,
        runtime=runtime,
        audit=audit,
        security=security,
        clock=lambda: AT,
    )

    with pytest.raises(DomainError) as step_up:
        service.capture_once(
            _principal(step_up=False),
            catalog_entry_id=approved.id,
            trace_id="trace-step-up",
        )
    assert step_up.value.code == "ADMIN_STEP_UP_REQUIRED"
    assert runtime.calls == []
    assert audit.list_entries() == ()

    blocked_service = ApprovedPublicFeedManualCaptureService(
        catalog=catalog,
        runtime=runtime,
        audit=FailingAuditRepository(),
        security=security,
        clock=lambda: AT,
    )
    with pytest.raises(DomainError) as audit_unavailable:
        blocked_service.capture_once(
            _principal(),
            catalog_entry_id=approved.id,
            trace_id="trace-step-up",
        )
    assert audit_unavailable.value.code == (
        "PUBLIC_FEED_MANUAL_CAPTURE_AUDIT_UNAVAILABLE"
    )
    assert runtime.calls == []


def test_one_invocation_emits_one_runtime_attempt_and_two_audit_events() -> None:
    catalog, security, principal, approved = _approved_catalog()
    command = approved.definition.acquisition_command()
    runtime = RecordingRuntime(
        SourceAcquisitionResult(
            outcome=SourceAcquisitionOutcome.BLOCKED,
            adapter_code=approved.adapter_code,
            pipeline_code=command.pipeline_code,
            pipeline_version=command.pipeline_version,
            trace_id="trace-one-attempt",
            duration_ms=7,
            error_code="SOURCE_PROVIDER_PAUSED",
        )
    )
    audit = InMemoryPublicFeedManualCaptureAuditRepository()
    service = ApprovedPublicFeedManualCaptureService(
        catalog=catalog,
        runtime=runtime,
        audit=audit,
        security=security,
        clock=lambda: AT,
    )

    result = service.capture_once(
        principal,
        catalog_entry_id=approved.id,
        trace_id="trace-one-attempt",
    )

    assert result.outcome is SourceAcquisitionOutcome.BLOCKED
    assert len(runtime.calls) == 1
    definition, trace_id, at = runtime.calls[0]
    assert definition == approved.definition
    assert trace_id == "trace-one-attempt"
    assert at == AT
    events = audit.list_entries(approved.id)
    assert [event.outcome for event in events] == [
        "ATTEMPT_STARTED",
        "BLOCKED",
    ]
    assert events[0].execution_id == events[1].execution_id == result.execution_id
    assert events[1].error_code == "SOURCE_PROVIDER_PAUSED"
    assert "approved.example.test" not in repr(events)


def test_runtime_exception_is_bounded_and_terminally_audited() -> None:
    catalog, security, principal, approved = _approved_catalog()
    runtime = RecordingRuntime(RuntimeError("private locator and backend details"))
    audit = InMemoryPublicFeedManualCaptureAuditRepository()
    service = ApprovedPublicFeedManualCaptureService(
        catalog=catalog,
        runtime=runtime,
        audit=audit,
        security=security,
        clock=lambda: AT,
    )

    result = service.capture_once(
        principal,
        catalog_entry_id=approved.id,
        trace_id="trace-runtime-failure",
    )

    assert result.outcome is SourceAcquisitionOutcome.FINAL_FAILURE
    assert result.error_code == "PUBLIC_FEED_MANUAL_CAPTURE_UNEXPECTED"
    events = audit.list_entries(approved.id)
    assert [item.outcome for item in events] == [
        "ATTEMPT_STARTED",
        "FINAL_FAILURE",
    ]
    assert "private locator" not in repr(result)
    assert "private locator" not in repr(events)


def test_full_approved_capture_commits_source_and_only_queues_ingestion() -> None:
    catalog, security, principal, approved = _approved_catalog()
    dns = FakeDnsResolver()
    backend = FakePinnedBackend((_raw_rss_response(),))
    http_observer = InMemoryProviderHttpObserver()
    evidence = InMemoryRawSourceEvidenceStore()
    knowledge = InMemoryKnowledgeRepository()
    ingestion_repository = InMemoryIngestionOrchestrationRepository()
    ingestion = IngestionOrchestrationService(ingestion_repository)
    provider_repository = InMemorySourceProviderAdmissionRepository()
    provider_admission = SourceProviderAdmissionService(provider_repository)
    runtime = InvocationScopedPublicFeedManualCaptureRuntime(
        http_runtime=ProviderHttpRuntimeComponents(
            mode=ProviderHttpRuntimeMode.EXTERNAL_PINNED,
            dns_resolver=dns,
            backend=backend,
        ),
        http_observer=http_observer,
        evidence_store=evidence,
        knowledge_repository=knowledge,
        ingestion_service=ingestion,
        provider_admission=provider_admission,
        provider_contexts=provider_repository,
        acquisition_observer=NoOpSourceAcquisitionObserver(),
    )
    audit = InMemoryPublicFeedManualCaptureAuditRepository()
    service = ApprovedPublicFeedManualCaptureService(
        catalog=catalog,
        runtime=runtime,
        audit=audit,
        security=security,
        clock=lambda: AT,
    )

    result = service.capture_once(
        principal,
        catalog_entry_id=approved.id,
        trace_id="trace-approved-vertical",
    )

    assert result.outcome is SourceAcquisitionOutcome.ADMITTED
    assert result.source_artifact_id is not None
    assert result.ingestion_run_id is not None
    assert dns.calls == ["approved.example.test"]
    assert len(backend.requests) == 1
    assert backend.requests[0].target_ip == "8.8.8.8"
    assert backend.requests[0].request_target == "/feed.xml"
    artifact = knowledge.get_source_artifact(result.source_artifact_id)
    assert artifact is not None
    assert artifact.adapter_code == approved.adapter_code
    assert artifact.raw_storage_ref is not None
    assert evidence.object_count == 1
    run = ingestion_repository.get_run(result.ingestion_run_id)
    assert run is not None
    assert run.state is IngestionRunState.QUEUED
    assert ingestion_repository.list_stage_executions(run.id) == ()
    assert ingestion_repository.list_proposals(run.id) == ()
    capability = provider_repository.get(approved.adapter_code)
    assert capability.credential_mode is ProviderCredentialMode.PUBLIC
    assert capability.secret_ref is None
    events = audit.list_entries(approved.id)
    assert [item.outcome for item in events] == [
        "ATTEMPT_STARTED",
        "ADMITTED",
    ]
    assert events[-1].source_artifact_id == result.source_artifact_id
    assert events[-1].ingestion_run_id == result.ingestion_run_id
