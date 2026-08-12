from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.identity.models import TokenResolution
from kefe_api.modules.identity.session_renewal import (
    RenewalResolution,
    SessionRotationMutation,
)


class IdentityRepository(Protocol):
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
    ) -> None: ...

    def resolve_token(
        self,
        *,
        token_hash: str,
        now: datetime,
    ) -> TokenResolution: ...

    def resolve_renewal(
        self,
        *,
        renewal_token_hash: str,
        now: datetime,
    ) -> RenewalResolution: ...

    def rotate_session(
        self,
        *,
        mutation: SessionRotationMutation,
    ) -> bool: ...

    def revoke_token(self, *, token_hash: str, now: datetime) -> None: ...
