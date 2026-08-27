from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.core.errors import DomainError
from kefe_api.core.settings import get_settings
from kefe_api.modules.identity.models import (
    ActorKind,
    ActorPrincipal,
    GuestCredential,
    TokenResolution,
    TokenStatus,
)
from kefe_api.modules.identity.ports import IdentityRepository
from kefe_api.modules.identity.session_renewal import (
    SessionContinuityPolicy,
    SessionTokenDeriver,
)


class IdentityService:
    def __init__(
        self,
        *,
        repository: IdentityRepository,
        guest_token_ttl_days: int,
        continuity_policy: SessionContinuityPolicy | None = None,
        token_deriver: SessionTokenDeriver | None = None,
    ) -> None:
        runtime_settings = get_settings()
        self._repo = repository
        self._guest_token_ttl = timedelta(days=guest_token_ttl_days)
        self._continuity_policy = continuity_policy or SessionContinuityPolicy.from_days(
            access_ttl_days=guest_token_ttl_days,
            absolute_lifetime_days=runtime_settings.session_renewal_absolute_lifetime_days,
            inactivity_lifetime_days=runtime_settings.session_renewal_inactivity_days,
            previous_pair_grace_seconds=(
                runtime_settings.session_renewal_previous_pair_grace_seconds
            ),
        )
        self._token_deriver = token_deriver or SessionTokenDeriver(
            active_key_id=runtime_settings.session_renewal_active_key_id,
            active_secret=runtime_settings.session_renewal_secret,
            retained_keys=runtime_settings.session_renewal_retained_keys,
        )

    def create_guest(self) -> GuestCredential:
        now = datetime.now(UTC)
        actor_id = uuid4()
        session_id = uuid4()
        pair = self._token_deriver.derive_pair(
            session_id=session_id,
            actor_id=actor_id,
            actor_kind=ActorKind.GUEST,
            rotation_counter=0,
        )
        expires_at = now + self._guest_token_ttl
        absolute_expires_at, inactive_expires_at = self._continuity_policy.initial_deadlines(
            now=now
        )
        self._repo.create_guest_session(
            actor_id=actor_id,
            session_id=session_id,
            token_hash=self._hash_token(pair.access_token),
            expires_at=expires_at,
            renewal_token_hash=self._hash_token(pair.renewal_token),
            rotation_counter=pair.rotation_counter,
            token_derivation_key_id=pair.derivation_key_id,
            continuity_absolute_expires_at=absolute_expires_at,
            continuity_inactive_expires_at=inactive_expires_at,
        )
        return GuestCredential(
            actor_id=actor_id,
            access_token=pair.access_token,
            expires_at=expires_at,
            renewal_token=pair.renewal_token,
            rotation_counter=pair.rotation_counter,
        )

    def authenticate(self, authorization: str | None) -> ActorPrincipal:
        resolution = self._resolve_authorization(authorization)
        if resolution.status is TokenStatus.EXPIRED:
            raise DomainError("AUTH_TOKEN_EXPIRED", "Authentication token expired", 401)
        if resolution.status is TokenStatus.REVOKED:
            raise DomainError("AUTH_TOKEN_REVOKED", "Authentication token revoked", 401)
        if resolution.status is not TokenStatus.ACTIVE or resolution.principal is None:
            raise DomainError("AUTH_TOKEN_INVALID", "Authentication token invalid", 401)
        return resolution.principal

    def require_active_access_token(self, authorization: str | None) -> str:
        self.authenticate(authorization)
        return self._extract_bearer(authorization)

    def authenticate_guest_merge(self, authorization: str | None) -> TokenResolution:
        """Resolve active or revoked identity only for exact guest-merge replay validation."""

        resolution = self._resolve_authorization(authorization)
        if resolution.status is TokenStatus.EXPIRED:
            raise DomainError("AUTH_TOKEN_EXPIRED", "Authentication token expired", 401)
        if resolution.status is TokenStatus.INVALID or resolution.principal is None:
            raise DomainError("AUTH_TOKEN_INVALID", "Authentication token invalid", 401)
        if resolution.status not in (TokenStatus.ACTIVE, TokenStatus.REVOKED):
            raise DomainError("AUTH_TOKEN_INVALID", "Authentication token invalid", 401)
        return resolution

    def revoke(self, authorization: str | None) -> None:
        token = self._extract_bearer(authorization)
        self._repo.revoke_token(
            token_hash=self._hash_token(token),
            now=datetime.now(UTC),
        )

    def _resolve_authorization(self, authorization: str | None) -> TokenResolution:
        token = self._extract_bearer(authorization)
        return self._repo.resolve_token(
            token_hash=self._hash_token(token),
            now=datetime.now(UTC),
        )

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _extract_bearer(authorization: str | None) -> str:
        if not authorization:
            raise DomainError("AUTH_REQUIRED", "Authentication required", 401)
        scheme, separator, token = authorization.partition(" ")
        if separator != " " or scheme.lower() != "bearer" or not token.strip():
            raise DomainError("AUTH_TOKEN_INVALID", "Authentication token invalid", 401)
        return token.strip()
