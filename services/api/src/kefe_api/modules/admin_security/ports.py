from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.admin_security.models import AdminSessionResolution, IssuedAdminSession


class AdminSessionResolver(Protocol):
    def resolve(self, session_token: str) -> AdminSessionResolution: ...

    def mark_seen(self, session_id: UUID, *, seen_at: datetime) -> None: ...


class AdminSessionIssuer(Protocol):
    def issue(
        self,
        *,
        admin_subject_id: UUID,
        authenticated_at: datetime,
        mfa_satisfied_at: datetime,
        expires_at: datetime,
    ) -> IssuedAdminSession: ...

    def record_step_up(self, session_id: UUID, *, step_up_at: datetime) -> None: ...

    def revoke(self, session_id: UUID, *, revoked_at: datetime) -> None: ...


class AdminCsrfVerifier(Protocol):
    def verify(self, *, session_token: str, csrf_token: str) -> bool: ...


class AdminSessionStore(AdminSessionResolver, AdminSessionIssuer, AdminCsrfVerifier, Protocol):
    """Composite port used by runtime composition; domain services depend on narrower ports."""


class AdminSecurityAuditSink(Protocol):
    def authorization_denied(
        self,
        *,
        admin_subject_id: str | None,
        capability: str,
        reason: str,
    ) -> None: ...
