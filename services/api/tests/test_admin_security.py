from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.content_authoring import SecuredContentAuthoringService
from kefe_api.modules.admin_security.models import (
    AdminCapability,
    AdminPrincipal,
    AdminRole,
    AdminSessionResolution,
    AdminSessionStatus,
)
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.content_authoring.in_memory import InMemoryContentAuthoringRepository
from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    AuthoringIssue,
    AuthoringQuestion,
    CaseIdentity,
    ContentLifecycle,
)
from kefe_api.modules.content_authoring.registry import default_authoring_registry
from kefe_api.modules.content_authoring.service import ContentAuthoringService

NOW = datetime(2026, 7, 28, 8, 0, tzinfo=UTC)


class StaticSessionResolver:
    def __init__(self, resolutions: dict[str, AdminSessionResolution] | None = None) -> None:
        self.resolutions = resolutions or {}

    def resolve(self, session_token: str) -> AdminSessionResolution:
        return self.resolutions.get(
            session_token,
            AdminSessionResolution(AdminSessionStatus.INVALID),
        )


class CapturingSecurityAuditSink:
    def __init__(self) -> None:
        self.denials: list[tuple[str | None, str, str]] = []

    def authorization_denied(
        self,
        *,
        admin_subject_id: str | None,
        capability: str,
        reason: str,
    ) -> None:
        self.denials.append((admin_subject_id, capability, reason))


def _principal(
    *roles: AdminRole,
    step_up_minutes_ago: int | None = 1,
    mfa: bool = True,
    last_seen_minutes_ago: int = 1,
) -> AdminPrincipal:
    return AdminPrincipal(
        admin_subject_id=uuid4(),
        session_id=uuid4(),
        roles=frozenset(roles),
        direct_capabilities=frozenset(),
        authenticated_at=NOW - timedelta(hours=1),
        mfa_satisfied_at=NOW - timedelta(hours=1) if mfa else None,
        step_up_at=(
            NOW - timedelta(minutes=step_up_minutes_ago)
            if step_up_minutes_ago is not None
            else None
        ),
        expires_at=NOW + timedelta(hours=11),
        last_seen_at=NOW - timedelta(minutes=last_seen_minutes_ago),
    )


def _security(
    *,
    resolver: StaticSessionResolver | None = None,
    audit_sink: CapturingSecurityAuditSink | None = None,
) -> AdminSecurityService:
    return AdminSecurityService(
        session_resolver=resolver or StaticSessionResolver(),
        policy=default_admin_security_policy(),
        audit_sink=audit_sink,
    )


def _draft(case_id) -> AuthoringCaseVersion:
    question = AuthoringQuestion(
        id=uuid4(),
        stable_code="PRIMARY_DECISION",
        prompt="Which option?",
        response_type="SINGLE_CHOICE",
        response_schema={"options": ["A", "B"]},
    )
    issue = AuthoringIssue(
        id=uuid4(),
        code="PRIMARY_ISSUE",
        title="Primary issue",
        questions=(question,),
    )
    return AuthoringCaseVersion(
        id=uuid4(),
        case_id=case_id,
        version_no=1,
        state=ContentLifecycle.DRAFT,
        title="Admin security test Case",
        summary="Low-risk authoring security test.",
        base_format_code="DILEMMA",
        primary_domain_code="DAILY_LIFE",
        content_risk="L0",
        issues=(issue,),
    )


def _facade() -> tuple[SecuredContentAuthoringService, InMemoryContentAuthoringRepository]:
    repository = InMemoryContentAuthoringRepository()
    authoring = ContentAuthoringService(repository, default_authoring_registry())
    facade = SecuredContentAuthoringService(
        authoring=authoring,
        repository=repository,
        security=_security(),
    )
    return facade, repository


def test_active_admin_session_requires_mfa_and_is_separate_from_unknown_tokens() -> None:
    principal = _principal(AdminRole.EDITOR)
    resolver = StaticSessionResolver(
        {"admin-session": AdminSessionResolution(AdminSessionStatus.ACTIVE, principal)}
    )
    security = _security(resolver=resolver)

    assert security.authenticate("admin-session", now=NOW) == principal

    with pytest.raises(DomainError) as unknown:
        security.authenticate("consumer-or-unknown-token", now=NOW)
    assert unknown.value.code == "ADMIN_SESSION_INVALID"

    no_mfa = replace(principal, mfa_satisfied_at=None)
    resolver.resolutions["no-mfa"] = AdminSessionResolution(AdminSessionStatus.ACTIVE, no_mfa)
    with pytest.raises(DomainError) as missing_mfa:
        security.authenticate("no-mfa", now=NOW)
    assert missing_mfa.value.code == "ADMIN_MFA_REQUIRED"


def test_revoked_and_idle_expired_admin_sessions_are_denied() -> None:
    principal = _principal(AdminRole.EDITOR)
    idle = _principal(AdminRole.EDITOR, last_seen_minutes_ago=31)
    resolver = StaticSessionResolver(
        {
            "revoked": AdminSessionResolution(AdminSessionStatus.REVOKED, principal),
            "idle": AdminSessionResolution(AdminSessionStatus.ACTIVE, idle),
        }
    )
    security = _security(resolver=resolver)

    with pytest.raises(DomainError) as revoked:
        security.authenticate("revoked", now=NOW)
    assert revoked.value.code == "ADMIN_SESSION_REVOKED"

    with pytest.raises(DomainError) as expired:
        security.authenticate("idle", now=NOW)
    assert expired.value.code == "ADMIN_SESSION_EXPIRED"


def test_roles_are_least_privilege_and_publish_requires_recent_step_up() -> None:
    sink = CapturingSecurityAuditSink()
    security = _security(audit_sink=sink)
    editor = _principal(AdminRole.EDITOR)
    stale_publisher = _principal(AdminRole.PUBLISHER, step_up_minutes_ago=16)
    fresh_publisher = _principal(AdminRole.PUBLISHER, step_up_minutes_ago=5)
    access_admin = _principal(AdminRole.ACCESS_ADMIN)

    security.authorize(editor, AdminCapability.CONTENT_EDIT, now=NOW)

    with pytest.raises(DomainError) as editor_publish:
        security.authorize(editor, AdminCapability.CONTENT_PUBLISH, now=NOW)
    assert editor_publish.value.code == "ADMIN_FORBIDDEN"

    with pytest.raises(DomainError) as stale_step_up:
        security.authorize(stale_publisher, AdminCapability.CONTENT_PUBLISH, now=NOW)
    assert stale_step_up.value.code == "ADMIN_STEP_UP_REQUIRED"

    security.authorize(fresh_publisher, AdminCapability.CONTENT_PUBLISH, now=NOW)

    with pytest.raises(DomainError) as access_publish:
        security.authorize(access_admin, AdminCapability.CONTENT_PUBLISH, now=NOW)
    assert access_publish.value.code == "ADMIN_FORBIDDEN"
    assert {denial[2] for denial in sink.denials} == {
        "capability_not_granted",
        "step_up_required",
    }


def test_secured_authoring_derives_audit_identity_and_blocks_self_review() -> None:
    facade, repository = _facade()
    editor_reviewer = _principal(AdminRole.EDITOR, AdminRole.REVIEWER)
    independent_reviewer = _principal(AdminRole.REVIEWER)
    publisher = _principal(AdminRole.PUBLISHER, step_up_minutes_ago=1)
    identity = CaseIdentity(id=uuid4(), slug=f"admin-sec-{uuid4().hex[:8]}")
    draft = _draft(identity.id)

    facade.create_case(
        editor_reviewer,
        identity=identity,
        initial_version=draft,
        now=NOW,
    )
    facade.submit_for_review(editor_reviewer, draft.id, now=NOW)

    with pytest.raises(DomainError) as self_review:
        facade.approve(editor_reviewer, draft.id, now=NOW)
    assert self_review.value.code == "ADMIN_SEPARATION_OF_DUTIES"

    approved = facade.approve(independent_reviewer, draft.id, now=NOW)
    published = facade.publish(publisher, approved.id, now=NOW)
    assert published.state is ContentLifecycle.PUBLISHED

    actor_refs = [entry.actor_ref for entry in repository.list_audit(identity.id)]
    assert actor_refs[0] == editor_reviewer.audit_actor_ref
    assert actor_refs[1] == editor_reviewer.audit_actor_ref
    assert actor_refs[2] == independent_reviewer.audit_actor_ref
    assert actor_refs[3] == publisher.audit_actor_ref
    assert all(actor_ref.startswith("admin:") for actor_ref in actor_refs)


def test_stale_publisher_cannot_publish_through_secured_facade() -> None:
    facade, _ = _facade()
    editor = _principal(AdminRole.EDITOR)
    reviewer = _principal(AdminRole.REVIEWER)
    stale_publisher = _principal(AdminRole.PUBLISHER, step_up_minutes_ago=20)
    identity = CaseIdentity(id=uuid4(), slug=f"admin-step-{uuid4().hex[:8]}")
    draft = _draft(identity.id)

    facade.create_case(editor, identity=identity, initial_version=draft, now=NOW)
    facade.submit_for_review(editor, draft.id, now=NOW)
    approved = facade.approve(reviewer, draft.id, now=NOW)

    with pytest.raises(DomainError) as denied:
        facade.publish(stale_publisher, approved.id, now=NOW)
    assert denied.value.code == "ADMIN_STEP_UP_REQUIRED"


def test_no_admin_http_surface_is_registered_yet() -> None:
    from kefe_api.main import create_app

    paths = {getattr(route, "path", "") for route in create_app().routes}
    assert not any(path.startswith("/admin") for path in paths)
    assert not any("authoring" in path for path in paths)
