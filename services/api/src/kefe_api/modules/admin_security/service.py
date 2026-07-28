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
        self._session_resolver.mark_seen(principal.session_id, seen_at=current)
        return principal

    def authorize(
        self,
        principal: AdminPrincipal,
        capability: AdminCapability,
        *,
        now: datetime | None = None,
    ) -> None:
        current = now or datetime.now(UTC)
        self._assert_principal_assurance(principal, current=current)

        granted = (
            self._policy.capabilities_for_roles(principal.roles)
            | principal.direct_capabilities
        )
        if capability not in granted:
            self._deny(principal, capability, "capability_not_granted")
            raise DomainError(
                "ADMIN_FORBIDDEN",
                "Admin capability is not granted",
                403,
                meta={"required_capability": capability.value},
            )

        if capability in self._policy.step_up_capabilities:
            step_up_at = principal.step_up_at
            if step_up_at is None or current - step_up_at > self._policy.step_up_freshness:
                self._deny(principal, capability, "step_up_required")
                raise DomainError(
                    "ADMIN_STEP_UP_REQUIRED",
                    "Recent Admin step-up authentication is required",
                    403,
                    meta={"required_capability": capability.value},
                )

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
