from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.models import ActorKind
from kefe_api.modules.identity.ports import IdentityRepository
from kefe_api.modules.identity.session_renewal import (
    RenewalResolutionStatus,
    RenewalTokenMatch,
    SessionBootstrapMutation,
    SessionBootstrapStatus,
    SessionContinuityPolicy,
    SessionRotationMutation,
    SessionTokenDeriver,
)


@dataclass(frozen=True, slots=True)
class RenewedSessionCredential:
    actor_id: UUID
    actor_kind: ActorKind
    access_token: str
    access_expires_at: datetime
    renewal_token: str
    rotation_counter: int


class SessionRenewalService:
    def __init__(
        self,
        *,
        repository: IdentityRepository,
        policy: SessionContinuityPolicy,
        deriver: SessionTokenDeriver,
        account_access_ttl: timedelta | None = None,
    ) -> None:
        self._repo = repository
        self._policy = policy
        self._deriver = deriver
        self._account_access_ttl = account_access_ttl or policy.access_ttl

    def renew(self, *, renewal_token: str) -> RenewedSessionCredential:
        normalized = renewal_token.strip()
        if not normalized:
            raise DomainError("AUTH_RENEWAL_INVALID", "Renewal credential is invalid", 401)
        renewal_hash = self._deriver.token_hash(normalized)

        for _ in range(2):
            now = datetime.now(UTC)
            resolution = self._repo.resolve_renewal(
                renewal_token_hash=renewal_hash,
                now=now,
            )
            self._raise_for_resolution(resolution.status)
            snapshot = resolution.snapshot
            if snapshot is None:
                raise DomainError("AUTH_RENEWAL_INVALID", "Renewal credential is invalid", 401)

            if snapshot.token_match is RenewalTokenMatch.PREVIOUS_GRACE:
                return self._reproduce_current(snapshot=snapshot)

            next_counter = snapshot.rotation_counter + 1
            next_pair = self._deriver.derive_pair(
                session_id=snapshot.session_id,
                actor_id=snapshot.actor_id,
                actor_kind=snapshot.actor_kind,
                rotation_counter=next_counter,
            )
            access_ttl = self._access_ttl(snapshot.actor_kind)
            next_access_expires_at = now + access_ttl
            next_inactive_expires_at = self._policy.renewed_inactivity_deadline(
                now=now,
                absolute_expires_at=snapshot.continuity_absolute_expires_at,
            )
            mutation = SessionRotationMutation(
                session_id=snapshot.session_id,
                expected_rotation_counter=snapshot.rotation_counter,
                current_access_token_hash=snapshot.access_token_hash,
                current_renewal_token_hash=snapshot.renewal_token_hash,
                next_access_token_hash=self._deriver.token_hash(next_pair.access_token),
                next_renewal_token_hash=self._deriver.token_hash(next_pair.renewal_token),
                next_access_expires_at=next_access_expires_at,
                next_inactive_expires_at=next_inactive_expires_at,
                next_rotation_counter=next_counter,
                next_derivation_key_id=next_pair.derivation_key_id,
                previous_pair_valid_until=now + self._policy.previous_pair_grace,
                renewed_at=now,
            )
            if self._repo.rotate_session(mutation=mutation):
                return RenewedSessionCredential(
                    actor_id=snapshot.actor_id,
                    actor_kind=snapshot.actor_kind,
                    access_token=next_pair.access_token,
                    access_expires_at=next_access_expires_at,
                    renewal_token=next_pair.renewal_token,
                    rotation_counter=next_counter,
                )

        raise DomainError(
            "AUTH_RENEWAL_REPLAYED",
            "Renewal credential cannot be replayed",
            409,
        )

    def bootstrap(self, *, access_token: str) -> RenewedSessionCredential:
        normalized = access_token.strip()
        if not normalized:
            raise DomainError("AUTH_TOKEN_INVALID", "Authentication token invalid", 401)
        access_hash = self._deriver.token_hash(normalized)

        for _ in range(2):
            now = datetime.now(UTC)
            resolution = self._repo.resolve_bootstrap(
                access_token_hash=access_hash,
                now=now,
            )
            self._raise_for_bootstrap_resolution(resolution.status)
            snapshot = resolution.snapshot
            if snapshot is None:
                raise DomainError("AUTH_TOKEN_INVALID", "Authentication token invalid", 401)
            if resolution.status is SessionBootstrapStatus.ACTIVE_CURRENT:
                return self._reproduce_current(snapshot=snapshot)

            pair = self._deriver.derive_pair(
                session_id=snapshot.session_id,
                actor_id=snapshot.actor_id,
                actor_kind=snapshot.actor_kind,
                rotation_counter=0,
            )
            absolute_expires_at, inactive_expires_at = self._policy.initial_deadlines(now=now)
            mutation = SessionBootstrapMutation(
                session_id=snapshot.session_id,
                expected_access_token_hash=snapshot.access_token_hash,
                next_access_token_hash=self._deriver.token_hash(pair.access_token),
                next_renewal_token_hash=self._deriver.token_hash(pair.renewal_token),
                next_access_expires_at=now + self._access_ttl(snapshot.actor_kind),
                continuity_absolute_expires_at=absolute_expires_at,
                continuity_inactive_expires_at=inactive_expires_at,
                derivation_key_id=pair.derivation_key_id,
                previous_access_valid_until=now + self._policy.previous_pair_grace,
                bootstrapped_at=now,
            )
            if self._repo.bootstrap_session(mutation=mutation):
                return RenewedSessionCredential(
                    actor_id=snapshot.actor_id,
                    actor_kind=snapshot.actor_kind,
                    access_token=pair.access_token,
                    access_expires_at=mutation.next_access_expires_at,
                    renewal_token=pair.renewal_token,
                    rotation_counter=0,
                )

        raise DomainError(
            "AUTH_RENEWAL_REPLAYED",
            "Session continuity bootstrap did not converge",
            409,
        )

    def _reproduce_current(self, *, snapshot) -> RenewedSessionCredential:
        if snapshot.derivation_key_id is None or snapshot.renewal_token_hash is None:
            raise DomainError(
                "DEPENDENCY_TEMPORARILY_UNAVAILABLE",
                "Session credential derivation state is unavailable",
                503,
                retryable=True,
            )
        pair = self._deriver.derive_pair(
            session_id=snapshot.session_id,
            actor_id=snapshot.actor_id,
            actor_kind=snapshot.actor_kind,
            rotation_counter=snapshot.rotation_counter,
            key_id=snapshot.derivation_key_id,
        )
        if (
            self._deriver.token_hash(pair.access_token) != snapshot.access_token_hash
            or self._deriver.token_hash(pair.renewal_token) != snapshot.renewal_token_hash
        ):
            raise DomainError(
                "DEPENDENCY_TEMPORARILY_UNAVAILABLE",
                "Session credential derivation state is unavailable",
                503,
                retryable=True,
            )
        return RenewedSessionCredential(
            actor_id=snapshot.actor_id,
            actor_kind=snapshot.actor_kind,
            access_token=pair.access_token,
            access_expires_at=snapshot.access_expires_at,
            renewal_token=pair.renewal_token,
            rotation_counter=snapshot.rotation_counter,
        )

    def _access_ttl(self, actor_kind: ActorKind) -> timedelta:
        if actor_kind is ActorKind.ACCOUNT:
            return self._account_access_ttl
        return self._policy.access_ttl

    @staticmethod
    def _raise_for_resolution(status: RenewalResolutionStatus) -> None:
        if status is RenewalResolutionStatus.ACTIVE:
            return
        if status is RenewalResolutionStatus.REVOKED:
            raise DomainError("AUTH_TOKEN_REVOKED", "Authentication session revoked", 401)
        if status is RenewalResolutionStatus.CONTINUITY_EXPIRED:
            raise DomainError(
                "AUTH_SESSION_CONTINUITY_EXPIRED",
                "Session continuity expired",
                401,
            )
        raise DomainError("AUTH_RENEWAL_INVALID", "Renewal credential is invalid", 401)

    @staticmethod
    def _raise_for_bootstrap_resolution(status: SessionBootstrapStatus) -> None:
        if status in (
            SessionBootstrapStatus.ACTIVE_LEGACY,
            SessionBootstrapStatus.ACTIVE_CURRENT,
        ):
            return
        if status is SessionBootstrapStatus.EXPIRED:
            raise DomainError("AUTH_TOKEN_EXPIRED", "Authentication token expired", 401)
        if status is SessionBootstrapStatus.REVOKED:
            raise DomainError("AUTH_TOKEN_REVOKED", "Authentication token revoked", 401)
        raise DomainError("AUTH_TOKEN_INVALID", "Authentication token invalid", 401)
