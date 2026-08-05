from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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
        self._actor_kinds: dict[UUID, ActorKind] = {}
        self._merged_into: dict[UUID, UUID] = {}
        self._lock = RLock()

    def create_guest_session(
        self,
        *,
        actor_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        with self._lock:
            self._actor_kinds.setdefault(actor_id, ActorKind.GUEST)
            self._sessions[token_hash] = _Session(actor_id=actor_id, expires_at=expires_at)

    def create_account_session(
        self,
        *,
        actor_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        with self._lock:
            self._actor_kinds[actor_id] = ActorKind.ACCOUNT
            self._sessions[token_hash] = _Session(actor_id=actor_id, expires_at=expires_at)

    def promote_or_merge_actor(
        self,
        *,
        guest_actor_id: UUID,
        account_actor_id: UUID,
        now: datetime | None = None,
    ) -> None:
        revoked_at = now or datetime.now(UTC)
        with self._lock:
            self._actor_kinds[account_actor_id] = ActorKind.ACCOUNT

            # Account conversion is a credential-rotation boundary. Every bearer issued
            # to the source guest must stop working before the new account credential is
            # created; otherwise a copied guest token silently inherits account access.
            for session in self._sessions.values():
                if session.actor_id == guest_actor_id:
                    session.revoked_at = session.revoked_at or revoked_at

            if guest_actor_id != account_actor_id:
                self._merged_into[guest_actor_id] = account_actor_id
                self._actor_kinds.pop(guest_actor_id, None)
            else:
                self._actor_kinds[guest_actor_id] = ActorKind.ACCOUNT

    def delete_actor(self, actor_id: UUID, *, now: datetime) -> None:
        with self._lock:
            for session in self._sessions.values():
                if session.actor_id == actor_id:
                    session.revoked_at = session.revoked_at or now
            self._merged_into = {
                guest_actor_id: account_actor_id
                for guest_actor_id, account_actor_id in self._merged_into.items()
                if guest_actor_id != actor_id and account_actor_id != actor_id
            }
            self._actor_kinds.pop(actor_id, None)

    def resolve_token(self, *, token_hash: str, now: datetime) -> TokenResolution:
        with self._lock:
            session = self._sessions.get(token_hash)
            if session is None:
                return TokenResolution(TokenStatus.INVALID)
            if session.revoked_at is not None:
                # Generic authentication still rejects REVOKED. The principal is retained
                # only so the guest-merge boundary can validate an exact completed replay.
                return TokenResolution(
                    TokenStatus.REVOKED,
                    ActorPrincipal(
                        actor_id=session.actor_id,
                        actor_kind=self._actor_kinds.get(session.actor_id, ActorKind.GUEST),
                    ),
                )
            if session.expires_at <= now:
                return TokenResolution(TokenStatus.EXPIRED)
            actor_id = self._merged_into.get(session.actor_id, session.actor_id)
            return TokenResolution(
                TokenStatus.ACTIVE,
                ActorPrincipal(
                    actor_id=actor_id,
                    actor_kind=self._actor_kinds.get(actor_id, ActorKind.GUEST),
                ),
            )

    def revoke_token(self, *, token_hash: str, now: datetime) -> None:
        with self._lock:
            session = self._sessions.get(token_hash)
            if session is not None:
                session.revoked_at = now
