from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from uuid import UUID, uuid4

from kefe_api.modules.admin_security.models import (
    AdminCapability,
    AdminPrincipal,
    AdminRole,
    AdminSessionResolution,
    AdminSessionStatus,
    AdminSubjectState,
    IssuedAdminSession,
)


@dataclass(slots=True)
class _SessionRecord:
    session_id: UUID
    subject_id: UUID
    token_hash: str
    csrf_hash: str
    authenticated_at: datetime
    mfa_satisfied_at: datetime
    step_up_at: datetime | None
    expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None = None


class InMemoryAdminSessionStore:
    """Test/dev adapter with the same opaque-session semantics as PostgreSQL."""

    def __init__(self) -> None:
        self._subjects: dict[UUID, AdminSubjectState] = {}
        self._roles: dict[UUID, set[AdminRole]] = {}
        self._capabilities: dict[UUID, set[AdminCapability]] = {}
        self._sessions_by_hash: dict[str, _SessionRecord] = {}
        self._sessions_by_id: dict[UUID, _SessionRecord] = {}
        self._lock = RLock()

    def provision_subject(
        self,
        subject_id: UUID,
        *,
        state: AdminSubjectState = AdminSubjectState.ACTIVE,
    ) -> None:
        with self._lock:
            self._subjects[subject_id] = state
            self._roles.setdefault(subject_id, set())
            self._capabilities.setdefault(subject_id, set())

    def set_subject_state(self, subject_id: UUID, state: AdminSubjectState) -> None:
        with self._lock:
            if subject_id not in self._subjects:
                raise ValueError("Admin subject not found")
            self._subjects[subject_id] = state

    def grant_role(self, subject_id: UUID, role: AdminRole) -> None:
        with self._lock:
            self._require_subject(subject_id)
            self._roles.setdefault(subject_id, set()).add(role)

    def grant_capability(self, subject_id: UUID, capability: AdminCapability) -> None:
        with self._lock:
            self._require_subject(subject_id)
            self._capabilities.setdefault(subject_id, set()).add(capability)

    def issue(
        self,
        *,
        admin_subject_id: UUID,
        authenticated_at: datetime,
        mfa_satisfied_at: datetime,
        expires_at: datetime,
    ) -> IssuedAdminSession:
        if expires_at <= authenticated_at:
            raise ValueError("Admin session expiry must be after authentication")
        with self._lock:
            if self._subjects.get(admin_subject_id) is not AdminSubjectState.ACTIVE:
                raise ValueError("Admin subject is not active")
            token = secrets.token_urlsafe(32)
            csrf = secrets.token_urlsafe(32)
            record = _SessionRecord(
                session_id=uuid4(),
                subject_id=admin_subject_id,
                token_hash=self._digest(token),
                csrf_hash=self._digest(csrf),
                authenticated_at=authenticated_at,
                mfa_satisfied_at=mfa_satisfied_at,
                step_up_at=None,
                expires_at=expires_at,
                last_seen_at=authenticated_at,
            )
            self._sessions_by_hash[record.token_hash] = record
            self._sessions_by_id[record.session_id] = record
            return IssuedAdminSession(
                session_id=record.session_id,
                session_token=token,
                csrf_token=csrf,
                expires_at=expires_at,
            )

    def resolve(self, session_token: str) -> AdminSessionResolution:
        with self._lock:
            record = self._sessions_by_hash.get(self._digest(session_token))
            if record is None:
                return AdminSessionResolution(AdminSessionStatus.INVALID)
            if record.revoked_at is not None:
                return AdminSessionResolution(AdminSessionStatus.REVOKED)
            if self._subjects.get(record.subject_id) is not AdminSubjectState.ACTIVE:
                return AdminSessionResolution(AdminSessionStatus.REVOKED)
            principal = AdminPrincipal(
                admin_subject_id=record.subject_id,
                session_id=record.session_id,
                roles=frozenset(self._roles.get(record.subject_id, set())),
                direct_capabilities=frozenset(
                    self._capabilities.get(record.subject_id, set())
                ),
                authenticated_at=record.authenticated_at,
                mfa_satisfied_at=record.mfa_satisfied_at,
                step_up_at=record.step_up_at,
                expires_at=record.expires_at,
                last_seen_at=record.last_seen_at,
            )
            return AdminSessionResolution(AdminSessionStatus.ACTIVE, principal)

    def mark_seen(self, session_id: UUID, *, seen_at: datetime) -> None:
        with self._lock:
            record = self._sessions_by_id.get(session_id)
            if record is not None and record.revoked_at is None:
                record.last_seen_at = max(record.last_seen_at, seen_at)

    def verify(self, *, session_token: str, csrf_token: str) -> bool:
        with self._lock:
            record = self._sessions_by_hash.get(self._digest(session_token))
            if record is None or record.revoked_at is not None:
                return False
            if self._subjects.get(record.subject_id) is not AdminSubjectState.ACTIVE:
                return False
            return hmac.compare_digest(record.csrf_hash, self._digest(csrf_token))

    def record_step_up(self, session_id: UUID, *, step_up_at: datetime) -> None:
        with self._lock:
            record = self._sessions_by_id.get(session_id)
            if record is None or record.revoked_at is not None:
                raise ValueError("Active Admin session was not found")
            record.step_up_at = step_up_at

    def revoke(self, session_id: UUID, *, revoked_at: datetime) -> None:
        with self._lock:
            record = self._sessions_by_id.get(session_id)
            if record is not None and record.revoked_at is None:
                record.revoked_at = revoked_at

    def _require_subject(self, subject_id: UUID) -> None:
        if subject_id not in self._subjects:
            raise ValueError("Admin subject not found")

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
