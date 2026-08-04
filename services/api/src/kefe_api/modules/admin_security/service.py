from __future__ import annotations

from datetime import UTC, datetime

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import (
    AdminCapability,
    AdminPrincipal,
    AdminSessionStatus,
)
from kefe_api.modules.admin_security.policy import AdminSecurityPolicy
from kefe_api.modules.admin_security.ports import AdminSecurityAuditSink, AdminSessionResolver


class NullAdminSecurityAuditSink:
    def authorization_denied(
        self,
        *,
        admin_subject_id: str | None,
        capability: str,
        reason: str,
    ) -> None:
        return None


class AdminSecurityService:
    def __init__(
        self,
        *,
        session_resolver: AdminSessionResolver,
        policy: AdminSecurityPolicy,
        audit_sink: AdminSecurityAuditSink | None = None,
    ) -> None:
        self._session_resolver = session_resolver
        self._policy = policy
        self._audit_sink = audit_sink or NullAdminSecurityAuditSink()

    def authenticate(
        self,
        session_token: str | None,
        *,
        now: datetime | None = None,
    ) -> AdminPrincipal:
        current = now or datetime.now(UTC)
        principal = self.resolve_session(session_token, now=current)
        self.touch(principal, now=current)
        return principal

    def resolve_session(
        self,
        session_token: str | None,
        *,
        now: datetime | None = None,
    ) -> AdminPrincipal:
        if not session_token:
            raise DomainError("ADMIN_AUTH_REQUIRED", "Admin authentication is required", 401)

        current = now or datetime.now(UTC)
        resolution = self._session_resolver.resolve(session_token)
        if resolution.status is AdminSessionStatus.REVOKED:
            raise DomainError("ADMIN_SESSION_REVOKED", "Admin session is revoked", 401)
        if resolution.status is AdminSessionStatus.EXPIRED:
            raise DomainError("ADMIN_SESSION_EXPIRED", "Admin session is expired", 401)
        if resolution.status is AdminSessionStatus.INVALID or resolution.principal is None:
            raise DomainError("ADMIN_SESSION_INVALID", "Admin session is invalid", 401)

        principal = resolution.principal
        self._assert_principal_assurance(principal, current=current)
        return principal

    def touch(
        self,
        principal: AdminPrincipal,
        *,
        now: datetime | None = None,
    ) -> None:
        current = now or datetime.now(UTC)
        self._assert_principal_assurance(principal, current=current)
        self._session_resolver.mark_seen(principal.session_id, seen_at=current)

    def authorize(
        self,
        principal: AdminPrincipal,
        capability: AdminCapability,
        *,
        now: datetime | None = None,
    ) -> None:
        current = now or datetime.now(UTC)
        self._assert_principal_assurance(principal, current=current)
        granted = self._granted_capabilities(principal)
        if capability not in granted:
            self._deny(principal, capability, "capability_not_granted")
            raise DomainError(
                "ADMIN_FORBIDDEN",
                "Admin capability is not granted",
                403,
                meta={"required_capability": capability.value},
            )
        self._require_step_up(principal, capability, current=current)

    def authorize_any(
        self,
        principal: AdminPrincipal,
        capabilities: frozenset[AdminCapability],
        *,
        now: datetime | None = None,
    ) -> AdminCapability:
        if not capabilities:
            raise ValueError("at least one Admin capability is required")
        current = now or datetime.now(UTC)
        self._assert_principal_assurance(principal, current=current)
        granted = self._granted_capabilities(principal)
        matching = sorted(
            granted.intersection(capabilities),
            key=lambda capability: capability.value,
        )
        if not matching:
            representative = sorted(capabilities, key=lambda capability: capability.value)[0]
            self._deny(principal, representative, "capability_not_granted")
            raise DomainError(
                "ADMIN_FORBIDDEN",
                "None of the required Admin capabilities is granted",
                403,
                meta={
                    "required_any_capabilities": sorted(
                        capability.value for capability in capabilities
                    )
                },
            )
        selected = matching[0]
        self._require_step_up(principal, selected, current=current)
        return selected

    def enforce_reviewer_separation(
        self,
        *,
        principal: AdminPrincipal,
        submitter_actor_ref: str | None,
    ) -> None:
        if not self._policy.reviewer_must_differ_from_submitter:
            return
        if submitter_actor_ref == principal.audit_actor_ref:
            self._deny(principal, AdminCapability.CONTENT_REVIEW, "self_review")
            raise DomainError(
                "ADMIN_SEPARATION_OF_DUTIES",
                "The submitting Admin cannot approve the same CaseVersion",
                403,
            )

    def _granted_capabilities(
        self,
        principal: AdminPrincipal,
    ) -> frozenset[AdminCapability]:
        return (
            self._policy.capabilities_for_roles(principal.roles)
            | principal.direct_capabilities
        )

    def _require_step_up(
        self,
        principal: AdminPrincipal,
        capability: AdminCapability,
        *,
        current: datetime,
    ) -> None:
        if capability not in self._policy.step_up_capabilities:
            return
        step_up_at = principal.step_up_at
        if step_up_at is None or current - step_up_at > self._policy.step_up_freshness:
            self._deny(principal, capability, "step_up_required")
            raise DomainError(
                "ADMIN_STEP_UP_REQUIRED",
                "Recent Admin step-up authentication is required",
                403,
                meta={"required_capability": capability.value},
            )

    def _assert_principal_assurance(
        self,
        principal: AdminPrincipal,
        *,
        current: datetime,
    ) -> None:
        if current >= principal.expires_at:
            raise DomainError("ADMIN_SESSION_EXPIRED", "Admin session is expired", 401)
        if current - principal.authenticated_at > self._policy.absolute_lifetime:
            raise DomainError("ADMIN_SESSION_EXPIRED", "Admin session exceeded its lifetime", 401)
        if current - principal.last_seen_at > self._policy.idle_timeout:
            raise DomainError("ADMIN_SESSION_EXPIRED", "Admin session is idle-expired", 401)
        if principal.mfa_satisfied_at is None:
            raise DomainError("ADMIN_MFA_REQUIRED", "Admin MFA assurance is required", 403)

    def _deny(
        self,
        principal: AdminPrincipal,
        capability: AdminCapability,
        reason: str,
    ) -> None:
        self._audit_sink.authorization_denied(
            admin_subject_id=str(principal.admin_subject_id),
            capability=capability.value,
            reason=reason,
        )
