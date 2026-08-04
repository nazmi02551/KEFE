from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import (
    AdminCapability,
    AdminPrincipal,
    AdminRole,
)
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.knowledge.canonical_public_feed_catalog import (
    CanonicalPublicFeedCatalogService,
    InMemoryPublicFeedCatalogRepository,
    InMemoryPublicFeedRuntimeProfileRegistry,
    PublicFeedActivationState,
    PublicFeedCatalogState,
)
from kefe_api.modules.knowledge.provider_control import (
    ProviderCapabilityLifecycle,
)
from kefe_api.modules.knowledge.provider_control_memory import (
    InMemorySourceProviderAdmissionRepository,
)
from kefe_api.modules.knowledge.provider_control_service import (
    SourceProviderAdmissionService,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import (
    StrictRssAtomParseProfile,
)
from kefe_api.modules.knowledge.source_scheduler import (
    SourceAcquisitionScheduleState,
)
from kefe_api.modules.knowledge.source_scheduler_memory import (
    InMemorySourceAcquisitionSchedulerRepository,
)
from kefe_api.modules.knowledge.source_scheduler_service import (
    NoOpSourceDispatchObserver,
    SourceAcquisitionSchedulerService,
)

NOW = datetime(2026, 8, 4, 11, 0, tzinfo=UTC)


class _UnusedSessionResolver:
    def resolve(self, session_token: str):  # pragma: no cover - authorization only
        raise AssertionError(session_token)

    def mark_seen(self, session_id, *, seen_at):  # pragma: no cover - authorization only
        return None


def _principal(
    role: AdminRole,
    *,
    direct: frozenset[AdminCapability] = frozenset(),
    subject_id=None,
) -> AdminPrincipal:
    current = datetime.now(UTC)
    return AdminPrincipal(
        admin_subject_id=subject_id or uuid4(),
        session_id=uuid4(),
        roles=frozenset({role}),
        direct_capabilities=direct,
        authenticated_at=current - timedelta(minutes=5),
        mfa_satisfied_at=current - timedelta(minutes=5),
        step_up_at=current - timedelta(minutes=2),
        expires_at=current + timedelta(hours=2),
        last_seen_at=current - timedelta(minutes=1),
    )


def _definition(version: int, *, locator_suffix: str = "") -> PublicFeedDefinition:
    return PublicFeedDefinition(
        feed_code="example-news",
        display_name="Example News",
        adapter_code=f"kefe.public_feed.example-news.v{version}",
        external_locator=f"https://feeds.example.test/news{locator_suffix}.xml",
        parser_profile=StrictRssAtomParseProfile(),
        connect_timeout_ms=1500,
        read_timeout_ms=3000,
        total_timeout_ms=5000,
        max_response_bytes=2_000_000,
        max_redirect_hops=2,
        terms_evidence_ref="evidence://provider-terms/example-news/v1",
        rate_limit_evidence_ref="evidence://provider-rate/example-news/v1",
        quota_limit=12,
        quota_window_seconds=60,
        failure_threshold=3,
        circuit_open_seconds=120,
        permit_ttl_seconds=30,
        language_code="tr",
        jurisdiction_code="TR",
    )


def _fixture():
    catalog = InMemoryPublicFeedCatalogRepository()
    provider_repository = InMemorySourceProviderAdmissionRepository()
    schedule_repository = InMemorySourceAcquisitionSchedulerRepository()
    runtime_profiles = InMemoryPublicFeedRuntimeProfileRegistry()
    security = AdminSecurityService(
        session_resolver=_UnusedSessionResolver(),
        policy=default_admin_security_policy(),
    )
    service = CanonicalPublicFeedCatalogService(
        repository=catalog,
        security=security,
        provider_admission=SourceProviderAdmissionService(provider_repository),
        runtime_profiles=runtime_profiles,
        scheduler=SourceAcquisitionSchedulerService(
            repository=schedule_repository,
            acquisition=object(),
            observer=NoOpSourceDispatchObserver(),
            clock=lambda: NOW,
        ),
        clock=lambda: NOW,
    )
    return service, catalog, provider_repository, schedule_repository, runtime_profiles


def test_versioned_maker_checker_catalog_and_exact_activation_replay() -> None:
    service, catalog, providers, schedules, profiles = _fixture()
    creator = _principal(AdminRole.REVIEWER)
    approver = _principal(AdminRole.ACCESS_ADMIN)

    draft = service.register_draft(
        creator,
        definition_version=1,
        definition=_definition(1),
        interval_seconds=900,
        max_dispatch_attempts=4,
    )
    assert draft.state is PublicFeedCatalogState.DRAFT
    assert providers.get(draft.definition.adapter_code) is None
    assert schedules.plan_due_once(at=NOW + timedelta(days=1)) is None
    assert profiles.get(draft.definition.adapter_code) is None

    preflight = service.preflight(
        creator,
        feed_code=draft.feed_code,
        definition_version=1,
    )
    assert preflight.configuration_hash == draft.configuration_hash
    assert preflight.allowed_origin == "https://feeds.example.test"
    assert providers.get(draft.definition.adapter_code) is None
    assert schedules.plan_due_once(at=NOW + timedelta(days=1)) is None

    self_approver = _principal(
        AdminRole.REVIEWER,
        direct=frozenset({AdminCapability.SOURCE_APPROVE}),
        subject_id=creator.admin_subject_id,
    )
    with pytest.raises(DomainError) as self_review:
        service.approve(
            self_approver,
            feed_code=draft.feed_code,
            definition_version=1,
            expected_configuration_hash=draft.configuration_hash,
        )
    assert self_review.value.code == "ADMIN_SEPARATION_OF_DUTIES"

    approved = service.approve(
        approver,
        feed_code=draft.feed_code,
        definition_version=1,
        expected_configuration_hash=draft.configuration_hash,
    )
    assert approved.state is PublicFeedCatalogState.APPROVED
    assert approved.created_by_actor_ref != approved.approved_by_actor_ref

    first = service.activate(
        approver,
        feed_code=draft.feed_code,
        definition_version=1,
        expected_configuration_hash=draft.configuration_hash,
        first_due_at=NOW + timedelta(minutes=1),
    )
    second = service.activate(
        approver,
        feed_code=draft.feed_code,
        definition_version=1,
        expected_configuration_hash=draft.configuration_hash,
        first_due_at=NOW + timedelta(minutes=10),
    )
    assert second == first
    assert first.state is PublicFeedActivationState.ACTIVE

    capability = providers.get(draft.definition.adapter_code)
    assert capability is not None
    assert capability.lifecycle_state is ProviderCapabilityLifecycle.ENABLED
    assert capability.secret_ref is None
    assert profiles.get(draft.definition.adapter_code) is not None

    schedule = schedules.get_schedule(first.schedule_id)
    assert schedule is not None
    assert schedule.state is SourceAcquisitionScheduleState.ACTIVE
    assert schedule.interval_seconds == 900
    assert schedule.max_dispatch_attempts == 4
    assert schedules.get_schedule(first.schedule_id) == schedule

    audit = catalog.list_audit(draft.id)
    assert [event.action.value for event in audit] == [
        "DRAFT_REGISTERED",
        "PREFLIGHT_SUCCEEDED",
        "APPROVED",
        "ACTIVATED",
    ]


def test_pause_resume_retire_and_new_version_only() -> None:
    service, catalog, providers, schedules, _profiles = _fixture()
    creator = _principal(AdminRole.REVIEWER)
    approver = _principal(AdminRole.ACCESS_ADMIN)

    draft = service.register_draft(
        creator,
        definition_version=1,
        definition=_definition(1),
        interval_seconds=600,
        max_dispatch_attempts=3,
    )
    service.preflight(creator, feed_code=draft.feed_code, definition_version=1)
    service.approve(
        approver,
        feed_code=draft.feed_code,
        definition_version=1,
        expected_configuration_hash=draft.configuration_hash,
    )
    active = service.activate(
        approver,
        feed_code=draft.feed_code,
        definition_version=1,
        expected_configuration_hash=draft.configuration_hash,
        first_due_at=NOW,
    )

    paused = service.pause(approver, feed_code=draft.feed_code, definition_version=1)
    assert paused.state is PublicFeedActivationState.PAUSED
    assert (
        providers.get(draft.definition.adapter_code).lifecycle_state
        is ProviderCapabilityLifecycle.PAUSED
    )
    assert schedules.get_schedule(active.schedule_id).state is SourceAcquisitionScheduleState.PAUSED

    resumed = service.resume(approver, feed_code=draft.feed_code, definition_version=1)
    assert resumed.state is PublicFeedActivationState.ACTIVE
    assert (
        providers.get(draft.definition.adapter_code).lifecycle_state
        is ProviderCapabilityLifecycle.ENABLED
    )

    retired_activation = service.retire_activation(
        approver,
        feed_code=draft.feed_code,
        definition_version=1,
    )
    assert retired_activation.state is PublicFeedActivationState.RETIRED
    assert (
        providers.get(draft.definition.adapter_code).lifecycle_state
        is ProviderCapabilityLifecycle.RETIRED
    )
    assert (
        schedules.get_schedule(active.schedule_id).state is SourceAcquisitionScheduleState.RETIRED
    )

    retired_definition = service.retire_definition(
        approver,
        feed_code=draft.feed_code,
        definition_version=1,
    )
    assert retired_definition.state is PublicFeedCatalogState.RETIRED

    with pytest.raises(DomainError) as skipped_version:
        service.register_draft(
            creator,
            definition_version=3,
            definition=_definition(3, locator_suffix="-v3"),
            interval_seconds=600,
            max_dispatch_attempts=3,
        )
    assert skipped_version.value.code == "ADMIN_PUBLIC_FEED_VERSION_CONFLICT"

    version_two = service.register_draft(
        creator,
        definition_version=2,
        definition=_definition(2, locator_suffix="-v2"),
        interval_seconds=1200,
        max_dispatch_attempts=5,
    )
    assert version_two.definition_version == 2
    assert version_two.configuration_hash != draft.configuration_hash
    assert [item.definition_version for item in catalog.list_definitions()] == [1, 2]
