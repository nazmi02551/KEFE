from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from uuid import UUID

from kefe_api.modules.identity.models import (
    ActorKind,
    ActorPrincipal,
    TokenResolution,
    TokenStatus,
)


@dataclass(slots=True)
class _Session:
    actor_id: UUID
    expires_at: datetime
    revoked_at: datetime | None = None


class InMemoryIdentityRepository:
    def __init__(self) -> None:
        self._sessions: dict[str, _Session] = {}
        self._lock = RLock()

    def create_guest_session(
        self,
        *,
        actor_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        with self._lock:
            self._sessions[token_hash] = _Session(actor_id=actor_id, expires_at=expires_at)

    def resolve_token(self, *, token_hash: str, now: datetime) -> TokenResolution:
        with self._lock:
            session = self._sessions.get(token_hash)
            if session is None:
                return TokenResolution(TokenStatus.INVALID)
            if session.revoked_at is not None:
                return TokenResolution(TokenStatus.REVOKED)
            if session.expires_at <= now:
                return TokenResolution(TokenStatus.EXPIRED)
            return TokenResolution(
                TokenStatus.ACTIVE,
                ActorPrincipal(actor_id=session.actor_id, actor_kind=ActorKind.GUEST),
            )

    def revoke_token(self, *, token_hash: str, now: datetime) -> None:
        with self._lock:
            session = self._sessions.get(token_hash)
            if session is not None:
                session.revoked_at = now
