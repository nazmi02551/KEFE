from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from uuid import UUID, uuid4

from kefe_api.modules.identity.models import (
    ActorKind,
    ActorPrincipal,
    TokenResolution,
    TokenStatus,
)
from kefe_api.modules.identity.session_renewal import (
    RenewalResolution,
    RenewalResolutionStatus,
    RenewalTokenMatch,
    SessionBootstrapMutation,
    SessionBootstrapResolution,
    SessionBootstrapSnapshot,
    SessionBootstrapStatus,
    SessionRenewalSnapshot,
    SessionRotationMutation,
)


@dataclass(slots=True)
class _Session:
    session_id: UUID
    actor_id: UUID
    token_hash: str
    expires_at: datetime
    revoked_at: datetime | None = None
    previous_token_hash: str | None = None
    previous_token_valid_until: datetime | None = None
    renewal_token_hash: str | None = None
    previous_renewal_token_hash: str | None = None
    previous_renewal_valid_until: datetime | None = None
    rotation_counter: int = 0
    token_derivation_key_id: str | None = None
    renewed_at: datetime | None = None
    continuity_absolute_expires_at: datetime | None = None
    continuity_inactive_expires_at: datetime | None = None


class InMemoryIdentityRepository:
    def __init__(self) -> None:
        self._sessions: dict[UUID, _Session] = {}
        self._actor_kinds: dict[UUID, ActorKind] = {}
        self._merged_into: dict[UUID, UUID] = {}
        self._lock = RLock()

    def create_guest_session(
        self,
        *,
        actor_id: UUID,
        token_hash: str,
        expires_at: datetime,
        session_id: UUID | None = None,
        renewal_token_hash: str | None = None,
        rotation_counter: int = 0,
        token_derivation_key_id: str | None = None,
        continuity_absolute_expires_at: datetime | None = None,
        continuity_inactive_expires_at: datetime | None = None,
    ) -> None:
        with self._lock:
            self._actor_kinds.setdefault(actor_id, ActorKind.GUEST)
            resolved_session_id = session_id or uuid4()
            self._sessions[resolved_session_id] = _Session(
                session_id=resolved_session_id,
                actor_id=actor_id,
                token_hash=token_hash,
                expires_at=expires_at,
                renewal_token_hash=renewal_token_hash,
                rotation_counter=rotation_counter,
                token_derivation_key_id=token_derivation_key_id,
                continuity_absolute_expires_at=continuity_absolute_expires_at,
                continuity_inactive_expires_at=continuity_inactive_expires_at,
            )

    def create_account_session(
        self,
        *,
        actor_id: UUID,
        token_hash: str,
        expires_at: datetime,
        session_id: UUID | None = None,
        renewal_token_hash: str | None = None,
        rotation_counter: int = 0,
        token_derivation_key_id: str | None = None,
        continuity_absolute_expires_at: datetime | None = None,
        continuity_inactive_expires_at: datetime | None = None,
    ) -> None:
        with self._lock:
            self._actor_kinds[actor_id] = ActorKind.ACCOUNT
            resolved_session_id = session_id or uuid4()
            self._sessions[resolved_session_id] = _Session(
                session_id=resolved_session_id,
                actor_id=actor_id,
                token_hash=token_hash,
                expires_at=expires_at,
                renewal_token_hash=renewal_token_hash,
                rotation_counter=rotation_counter,
                token_derivation_key_id=token_derivation_key_id,
                continuity_absolute_expires_at=continuity_absolute_expires_at,
                continuity_inactive_expires_at=continuity_inactive_expires_at,
            )

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
            session = self._find_access_session(token_hash=token_hash, now=now)
            if session is None:
                return TokenResolution(TokenStatus.INVALID)
            if session.revoked_at is not None:
                return TokenResolution(
                    TokenStatus.REVOKED,
                    ActorPrincipal(
                        actor_id=session.actor_id,
                        actor_kind=self._actor_kinds.get(session.actor_id, ActorKind.GUEST),
                    ),
                )
            if session.expires_at <= now and session.token_hash == token_hash:
                return TokenResolution(TokenStatus.EXPIRED)
            actor_id = self._merged_into.get(session.actor_id, session.actor_id)
            return TokenResolution(
                TokenStatus.ACTIVE,
                ActorPrincipal(
                    actor_id=actor_id,
                    actor_kind=self._actor_kinds.get(actor_id, ActorKind.GUEST),
                ),
            )

    def resolve_renewal(
        self,
        *,
        renewal_token_hash: str,
        now: datetime,
    ) -> RenewalResolution:
        with self._lock:
            for session in self._sessions.values():
                token_match: RenewalTokenMatch | None = None
                if session.renewal_token_hash == renewal_token_hash:
                    token_match = RenewalTokenMatch.CURRENT
                elif (
                    session.previous_renewal_token_hash == renewal_token_hash
                    and session.previous_renewal_valid_until is not None
                    and now <= session.previous_renewal_valid_until
                ):
                    token_match = RenewalTokenMatch.PREVIOUS_GRACE
                if token_match is None:
                    continue

                if session.revoked_at is not None:
                    return RenewalResolution(RenewalResolutionStatus.REVOKED)
                if (
                    session.continuity_absolute_expires_at is None
                    or session.continuity_inactive_expires_at is None
                    or session.token_derivation_key_id is None
                    or session.renewal_token_hash is None
                ):
                    return RenewalResolution(RenewalResolutionStatus.INVALID)
                if (
                    now >= session.continuity_absolute_expires_at
                    or now >= session.continuity_inactive_expires_at
                ):
                    return RenewalResolution(RenewalResolutionStatus.CONTINUITY_EXPIRED)

                actor_id = self._merged_into.get(session.actor_id, session.actor_id)
                actor_kind = self._actor_kinds.get(actor_id)
                if actor_kind is None:
                    return RenewalResolution(RenewalResolutionStatus.INVALID)
                return RenewalResolution(
                    RenewalResolutionStatus.ACTIVE,
                    SessionRenewalSnapshot(
                        session_id=session.session_id,
                        actor_id=actor_id,
                        actor_kind=actor_kind,
                        rotation_counter=session.rotation_counter,
                        derivation_key_id=session.token_derivation_key_id,
                        access_token_hash=session.token_hash,
                        renewal_token_hash=session.renewal_token_hash,
                        access_expires_at=session.expires_at,
                        continuity_absolute_expires_at=session.continuity_absolute_expires_at,
                        continuity_inactive_expires_at=session.continuity_inactive_expires_at,
                        token_match=token_match,
                    ),
                )
            return RenewalResolution(RenewalResolutionStatus.INVALID)

    def rotate_session(self, *, mutation: SessionRotationMutation) -> bool:
        with self._lock:
            session = self._sessions.get(mutation.session_id)
            if session is None or session.revoked_at is not None:
                return False
            if session.rotation_counter != mutation.expected_rotation_counter:
                return False
            if session.token_hash != mutation.current_access_token_hash:
                return False
            if session.renewal_token_hash != mutation.current_renewal_token_hash:
                return False
            if (
                session.continuity_absolute_expires_at is None
                or mutation.renewed_at >= session.continuity_absolute_expires_at
                or session.continuity_inactive_expires_at is None
                or mutation.renewed_at >= session.continuity_inactive_expires_at
            ):
                return False

            session.previous_token_hash = session.token_hash
            session.previous_token_valid_until = min(
                mutation.previous_pair_valid_until,
                session.expires_at,
            )
            session.previous_renewal_token_hash = session.renewal_token_hash
            session.previous_renewal_valid_until = mutation.previous_pair_valid_until
            session.token_hash = mutation.next_access_token_hash
            session.renewal_token_hash = mutation.next_renewal_token_hash
            session.expires_at = mutation.next_access_expires_at
            session.continuity_inactive_expires_at = mutation.next_inactive_expires_at
            session.rotation_counter = mutation.next_rotation_counter
            session.token_derivation_key_id = mutation.next_derivation_key_id
            session.renewed_at = mutation.renewed_at
            return True

    def resolve_bootstrap(
        self,
        *,
        access_token_hash: str,
        now: datetime,
    ) -> SessionBootstrapResolution:
        with self._lock:
            session = self._find_access_session(
                token_hash=access_token_hash,
                now=now,
            )
            if session is None:
                return SessionBootstrapResolution(SessionBootstrapStatus.INVALID)
            if session.revoked_at is not None:
                return SessionBootstrapResolution(SessionBootstrapStatus.REVOKED)
            if session.token_hash == access_token_hash and session.expires_at <= now:
                return SessionBootstrapResolution(SessionBootstrapStatus.EXPIRED)

            actor_id = self._merged_into.get(session.actor_id, session.actor_id)
            actor_kind = self._actor_kinds.get(actor_id)
            if actor_kind is None:
                return SessionBootstrapResolution(SessionBootstrapStatus.INVALID)

            renewal_fields = (
                session.renewal_token_hash,
                session.token_derivation_key_id,
                session.continuity_absolute_expires_at,
                session.continuity_inactive_expires_at,
            )
            if all(value is None for value in renewal_fields):
                if session.rotation_counter != 0 or session.token_hash != access_token_hash:
                    return SessionBootstrapResolution(SessionBootstrapStatus.INVALID)
                status = SessionBootstrapStatus.ACTIVE_LEGACY
            elif all(value is not None for value in renewal_fields):
                status = SessionBootstrapStatus.ACTIVE_CURRENT
            else:
                return SessionBootstrapResolution(SessionBootstrapStatus.INVALID)

            return SessionBootstrapResolution(
                status,
                SessionBootstrapSnapshot(
                    session_id=session.session_id,
                    actor_id=actor_id,
                    actor_kind=actor_kind,
                    rotation_counter=session.rotation_counter,
                    derivation_key_id=session.token_derivation_key_id,
                    access_token_hash=session.token_hash,
                    renewal_token_hash=session.renewal_token_hash,
                    access_expires_at=session.expires_at,
                    continuity_absolute_expires_at=(session.continuity_absolute_expires_at),
                    continuity_inactive_expires_at=(session.continuity_inactive_expires_at),
                ),
            )

    def bootstrap_session(self, *, mutation: SessionBootstrapMutation) -> bool:
        with self._lock:
            session = self._sessions.get(mutation.session_id)
            if session is None or session.revoked_at is not None:
                return False
            if session.token_hash != mutation.expected_access_token_hash:
                return False
            if session.expires_at <= mutation.bootstrapped_at:
                return False
            if (
                session.renewal_token_hash is not None
                or session.token_derivation_key_id is not None
                or session.continuity_absolute_expires_at is not None
                or session.continuity_inactive_expires_at is not None
                or session.rotation_counter != 0
            ):
                return False

            session.previous_token_hash = session.token_hash
            session.previous_token_valid_until = min(
                mutation.previous_access_valid_until,
                session.expires_at,
            )
            session.token_hash = mutation.next_access_token_hash
            session.renewal_token_hash = mutation.next_renewal_token_hash
            session.expires_at = mutation.next_access_expires_at
            session.token_derivation_key_id = mutation.derivation_key_id
            session.continuity_absolute_expires_at = mutation.continuity_absolute_expires_at
            session.continuity_inactive_expires_at = mutation.continuity_inactive_expires_at
            session.renewed_at = mutation.bootstrapped_at
            return True

    def revoke_token(self, *, token_hash: str, now: datetime) -> None:
        with self._lock:
            session = self._find_access_session(token_hash=token_hash, now=now)
            if session is not None:
                session.revoked_at = now

    def _find_access_session(self, *, token_hash: str, now: datetime) -> _Session | None:
        for session in self._sessions.values():
            if session.token_hash == token_hash:
                return session
            if (
                session.previous_token_hash == token_hash
                and session.previous_token_valid_until is not None
                and now <= session.previous_token_valid_until
            ):
                return session
        return None
