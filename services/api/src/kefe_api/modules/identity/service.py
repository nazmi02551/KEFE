from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.models import (
    ActorPrincipal,
    GuestCredential,
    TokenResolution,
    TokenStatus,
)
from kefe_api.modules.identity.ports import IdentityRepository


class IdentityService:
    def __init__(self, *, repository: IdentityRepository, guest_token_ttl_days: int) -> None:
        self._repo = repository
        self._guest_token_ttl = timedelta(days=guest_token_ttl_days)

    def create_guest(self) -> GuestCredential:
        actor_id = uuid4()
        token = f"kefe_g_{secrets.token_urlsafe(32)}"
        expires_at = datetime.now(UTC) + self._guest_token_ttl
        self._repo.create_guest_session(
            actor_id=actor_id,
            token_hash=self._hash_token(token),
            expires_at=expires_at,
        )
        return GuestCredential(actor_id=actor_id, access_token=token, expires_at=expires_at)

    def authenticate(self, authorization: str | None) -> ActorPrincipal:
        resolution = self._resolve_authorization(authorization)
        if resolution.status is TokenStatus.EXPIRED:
            raise DomainError("AUTH_TOKEN_EXPIRED", "Authentication token expired", 401)
        if resolution.status is TokenStatus.REVOKED:
            raise DomainError("AUTH_TOKEN_REVOKED", "Authentication token revoked", 401)
        if resolution.status is not TokenStatus.ACTIVE or resolution.principal is None:
            raise DomainError("AUTH_TOKEN_INVALID", "Authentication token invalid", 401)
        return resolution.principal

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
