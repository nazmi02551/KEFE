from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, replace
from datetime import UTC, datetime
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


@dataclass(frozen=True, slots=True)
class _Subject:
    state: AdminSubjectState
    roles: frozenset[AdminRole]
    capabilities: frozenset[AdminCapability]


@dataclass(frozen=True, slots=True)
class _Session:
    session_id: UUID
    subject_id: UUID
    token_hash: str
    csrf_hash: str
    authenticated_at: datetime
    mfa_satisfied_at: datetime | None
    step_up_at: datetime | None
    expires_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None = None


class InMemoryAdminSessionStore:
    """Development/test adapter implementing Admin session ports without raw-token persistence."""

    def __init__(self) -> None:
        self._subjects: dict[UUID, _Subject] = {}
        self._sessions_by_hash: dict[str, _Session] = {}
        self._session_hash_by_id: dict[UUID, str] = {}
        self._lock = RLock()

    def upsert_subject(
        self,
        subject_id: UUID,
        *,
        state: AdminSubjectState = AdminSubjectState.ACTIVE,
        roles: frozenset[AdminRole] = frozenset(),
        capabilities: frozenset[AdminCapability] = frozenset(),
    ) -> None:
        with self._lock:
            self._subjects[subject_id] = _Subject(
                state=state,
                roles=roles,
                capabilities=capabilities,
            )

    def set_subject_state(self, subject_id: UUID, state: AdminSubjectState) -> None:
        with self._lock:
            subject = self._subjects[subject_id]
            self._subjects[subject_id] = replace(subject, state=state)

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
            subject = self._subjects.get(admin_subject_id)
            if subject is None or subject.state is not AdminSubjectState.ACTIVE:
                raise ValueError("Admin subject is not active")

            session_token = secrets.token_urlsafe(32)
            csrf_token = secrets.token_urlsafe(32)
            session = _Session(
                session_id=uuid4(),
                subject_id=admin_subject_id,
                token_hash=self._digest(session_token),
                csrf_hash=self._digest(csrf_token),
                authenticated_at=authenticated_at,
                mfa_satisfied_at=mfa_satisfied_at,
                step_up_at=None,
                expires_at=expires_at,
                last_seen_at=authenticated_at,
            )
            self._sessions_by_hash[session.token_hash] = session
            self._session_hash_by_id[session.session_id] = session.token_hash
            return IssuedAdminSession(
                session_id=session.session_id,
                session_token=session_token,
                csrf_token=csrf_token,
                expires_at=expires_at,
            )

    def resolve(self, session_token: str) -> AdminSessionResolution:
        if not session_token:
            return AdminSessionResolution(AdminSessionStatus.INVALID)

        with self._lock:
            session = self._sessions_by_hash.get(self._digest(session_token))
            if session is None:
                return AdminSessionResolution(AdminSessionStatus.INVALID)
            subject = self._subjects.get(session.subject_id)
            if session.revoked_at is not None or subject is None:
                return AdminSessionResolution(AdminSessionStatus.REVOKED)
            if subject.state is not AdminSubjectState.ACTIVE:
                return AdminSessionResolution(AdminSessionStatus.REVOKED)
            if session.expires_at <= datetime.now(UTC):
                return AdminSessionResolution(AdminSessionStatus.EXPIRED)

            principal = AdminPrincipal(
                admin_subject_id=session.subject_id,
                session_id=session.session_id,
                roles=subject.roles,
                direct_capabilities=subject.capabilities,
                authenticated_at=session.authenticated_at,
                mfa_satisfied_at=session.mfa_satisfied_at,
                step_up_at=session.step_up_at,
                expires_at=session.expires_at,
                last_seen_at=session.last_seen_at,
            )
            return AdminSessionResolution(AdminSessionStatus.ACTIVE, principal)

    def mark_seen(self, session_id: UUID, *, seen_at: datetime) -> None:
        with self._lock:
            session = self._session_by_id(session_id)
            if session is None or session.revoked_at is not None:
                return
            self._replace_session(
                session,
                last_seen_at=max(session.last_seen_at, seen_at),
            )

    def verify(self, *, session_token: str, csrf_token: str) -> bool:
        if not session_token or not csrf_token:
            return False
        with self._lock:
            session = self._sessions_by_hash.get(self._digest(session_token))
            if session is None or session.revoked_at is not None:
                return False
            subject = self._subjects.get(session.subject_id)
            if subject is None or subject.state is not AdminSubjectState.ACTIVE:
                return False
            if session.expires_at <= datetime.now(UTC):
                return False
            return hmac.compare_digest(session.csrf_hash, self._digest(csrf_token))

    def record_step_up(self, session_id: UUID, *, step_up_at: datetime) -> None:
        with self._lock:
            session = self._session_by_id(session_id)
            if session is None or session.revoked_at is not None:
                raise ValueError("Active Admin session was not found")
            self._replace_session(session, step_up_at=step_up_at)

    def revoke(self, session_id: UUID, *, revoked_at: datetime) -> None:
        with self._lock:
            session = self._session_by_id(session_id)
            if session is None:
                return
            self._replace_session(session, revoked_at=session.revoked_at or revoked_at)

    def _session_by_id(self, session_id: UUID) -> _Session | None:
        token_hash = self._session_hash_by_id.get(session_id)
        return self._sessions_by_hash.get(token_hash) if token_hash else None

    def _replace_session(self, session: _Session, **changes) -> None:
        updated = replace(session, **changes)
        self._sessions_by_hash[session.token_hash] = updated

    @staticmethod
    def _digest(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
