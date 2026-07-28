from __future__ import annotations

from typing import Protocol

from kefe_api.modules.admin_security.models import AdminSessionResolution


class AdminSessionResolver(Protocol):
    def resolve(self, session_token: str) -> AdminSessionResolution: ...


class AdminSecurityAuditSink(Protocol):
    def authorization_denied(
        self,
        *,
        admin_subject_id: str | None,
        capability: str,
        reason: str,
    ) -> None: ...
