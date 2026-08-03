from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.in_memory import InMemoryAdminSessionStore
from kefe_api.modules.admin_security.models import (
    AdminCapability,
    AdminPrincipal,
    AdminRole,
)
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.knowledge.public_feed_catalog import (
    InMemoryPublicFeedCatalogRepository,
    PublicFeedCatalogConflictError,
    PublicFeedCatalogEntry,
    PublicFeedCatalogService,
    PublicFeedCatalogState,
)
from kefe_api.modules.knowledge.public_feed_runtime import PublicFeedDefinition
from kefe_api.modules.knowledge.rss_atom_capture import StrictRssAtomParseProfile

AT = datetime(2026, 8, 3, 16, 30, tzinfo=UTC)


def _definition(**overrides) -> PublicFeedDefinition:
    values = {
        "feed_code": "test.catalog_feed.v1",
        "display_name": "Catalog Test Feed",
        "adapter_code": "test.catalog_rss.v1",
        "external_locator": "https://catalog.example.test/feed.xml",
        "parser_profile": StrictRssAtomParseProfile(),
        "connect_timeout_ms": 1000,
        "read_timeout_ms": 1500,
        "total_timeout_ms": 3000,
        "max_response_bytes": 1_048_576,
        "max_redirect_hops": 2,
        "terms_evidence_ref": "evidence://terms/catalog-feed-v1",
        "rate_limit_evidence_ref": "evidence://rate/catalog-feed-v1",
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


def _principal(
    *,
    role: AdminRole = AdminRole.REVIEWER,
    step_up_at: datetime | None = AT,
    direct: frozenset[AdminCapability] = frozenset(),
) -> AdminPrincipal:
    return AdminPrincipal(
        admin_subject_id=uuid4(),
        session_id=uuid4(),
        roles=frozenset({role}),
        direct_capabilities=direct,
        authenticated_at=AT - timedelta(minutes=5),
        mfa_satisfied_at=AT - timedelta(minutes=5),
        step_up_at=step_up_at,
        expires_at=AT + timedelta(hours=8),
        last_seen_at=AT,
    )


def _service(repository=None) -> PublicFeedCatalogService:
    return PublicFeedCatalogService(
        repository=repository or InMemoryPublicFeedCatalogRepository(),
        security=AdminSecurityService(
            session_resolver=InMemoryAdminSessionStore(),
            policy=default_admin_security_policy(),
        ),
        clock=lambda: AT,
    )


def test_catalog_entry_is_immutable_and_lifecycle_is_one_way() -> None:
    definition = _definition()
    entry = PublicFeedCatalogEntry(
        id=uuid4(),
        definition=definition,
        configuration_hash=definition.configuration_hash,
        state=PublicFeedCatalogState.REGISTERED,
        registered_by="admin:test",
        registered_at=AT,
    )

    with pytest.raises(FrozenInstanceError):
        entry.state = PublicFeedCatalogState.RETIRED  # type: ignore[misc]

    approved = entry.transition(
        PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED,
        actor_ref="admin:approver",
        at=AT + timedelta(minutes=1),
    )
    retired = approved.transition(
        PublicFeedCatalogState.RETIRED,
        actor_ref="admin:retirer",
        at=AT + timedelta(minutes=2),
        rationale="Publisher contract changed.",
    )

    assert approved.definition is definition
    assert approved.configuration_hash == entry.configuration_hash
    assert retired.approved_by == "admin:approver"
    assert retired.retired_by == "admin:retirer"
    assert retired.retirement_rationale == "Publisher contract changed."
    with pytest.raises(ValueError, match="transition"):
        retired.transition(
            PublicFeedCatalogState.REGISTERED,
            actor_ref="admin:invalid",
            at=AT + timedelta(minutes=3),
        )


def test_registration_is_exactly_idempotent_without_duplicate_audit() -> None:
    repository = InMemoryPublicFeedCatalogRepository()
    service = _service(repository)
    principal = _principal(step_up_at=None)
    definition = _definition()

    first = service.register(principal, definition)
    second = service.register(principal, definition)

    assert second == first
    assert repository.list_entries() == (first,)
    audit = repository.list_audit()
    assert len(audit) == 1
    assert audit[0].command == "REGISTER"
    assert audit[0].previous_state is None
    assert audit[0].new_state is PublicFeedCatalogState.REGISTERED
    assert audit[0].actor_ref == principal.audit_actor_ref


def test_feed_and_adapter_conflicts_fail_closed() -> None:
    repository = InMemoryPublicFeedCatalogRepository()
    service = _service(repository)
    principal = _principal()
    first = service.register(principal, _definition())
    assert first.state is PublicFeedCatalogState.REGISTERED

    with pytest.raises(DomainError) as feed_conflict:
        service.register(
            principal,
            _definition(external_locator="https://other.example.test/feed.xml"),
        )
    assert feed_conflict.value.code == "PUBLIC_FEED_CATALOG_CONFLICT"

    with pytest.raises(DomainError) as adapter_conflict:
        service.register(
            principal,
            _definition(
                feed_code="test.other_catalog_feed.v1",
                external_locator="https://second.example.test/feed.xml",
            ),
        )
    assert adapter_conflict.value.code == "PUBLIC_FEED_CATALOG_CONFLICT"
    assert repository.list_entries() == (first,)
    assert len(repository.list_audit()) == 1


def test_source_manage_authorization_and_step_up_boundaries() -> None:
    repository = InMemoryPublicFeedCatalogRepository()
    service = _service(repository)
    editor = _principal(role=AdminRole.EDITOR, step_up_at=AT)
    reviewer_without_step_up = _principal(step_up_at=None)

    with pytest.raises(DomainError) as forbidden:
        service.register(editor, _definition())
    assert forbidden.value.code == "ADMIN_FORBIDDEN"
    assert repository.list_entries() == ()

    registered = service.register(reviewer_without_step_up, _definition())
    assert registered.state is PublicFeedCatalogState.REGISTERED

    with pytest.raises(DomainError) as step_up:
        service.approve_manual_capture(reviewer_without_step_up, registered.id)
    assert step_up.value.code == "ADMIN_STEP_UP_REQUIRED"
    assert repository.get(registered.id) == registered
    assert len(repository.list_audit()) == 1


def test_approval_retirement_and_ordered_audit_are_atomic() -> None:
    repository = InMemoryPublicFeedCatalogRepository()
    service = _service(repository)
    principal = _principal()

    registered = service.register(principal, _definition())
    approved = service.approve_manual_capture(principal, registered.id)
    retired = service.retire(
        principal,
        registered.id,
        rationale="Feed ownership changed.",
    )

    assert approved.state is PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED
    assert retired.state is PublicFeedCatalogState.RETIRED
    assert repository.get(registered.id) == retired
    audit = repository.list_audit(registered.id)
    assert [item.command for item in audit] == [
        "REGISTER",
        "APPROVE_MANUAL_CAPTURE",
        "RETIRE",
    ]
    assert [item.new_state for item in audit] == [
        PublicFeedCatalogState.REGISTERED,
        PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED,
        PublicFeedCatalogState.RETIRED,
    ]
    assert audit[-1].rationale == "Feed ownership changed."

    with pytest.raises(DomainError) as invalid:
        service.approve_manual_capture(principal, registered.id)
    assert invalid.value.code == "PUBLIC_FEED_CATALOG_TRANSITION_INVALID"
    assert len(repository.list_audit(registered.id)) == 3


def test_repository_rejects_stale_transition_without_partial_audit() -> None:
    repository = InMemoryPublicFeedCatalogRepository()
    service = _service(repository)
    principal = _principal()
    registered = service.register(principal, _definition())
    stale = replace(
        registered,
        state=PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED,
        approved_by=principal.audit_actor_ref,
        approved_at=AT,
    )
    service.approve_manual_capture(principal, registered.id)

    from kefe_api.modules.knowledge.public_feed_catalog import (
        PublicFeedCatalogAuditEntry,
    )

    with pytest.raises(PublicFeedCatalogConflictError):
        repository.transition(
            stale,
            PublicFeedCatalogAuditEntry(
                audit_id=uuid4(),
                catalog_entry_id=registered.id,
                feed_code=registered.feed_code,
                actor_ref=principal.audit_actor_ref,
                command="STALE_APPROVE",
                previous_state=PublicFeedCatalogState.REGISTERED,
                new_state=PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED,
                occurred_at=AT,
            ),
        )
    assert [item.command for item in repository.list_audit()] == [
        "REGISTER",
        "APPROVE_MANUAL_CAPTURE",
    ]
