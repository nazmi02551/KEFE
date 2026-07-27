from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.identity.models import TokenResolution


class IdentityRepository(Protocol):
    def create_guest_session(
        self,
        *,
        actor_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None: ...

    def resolve_token(
        self,
        *,
        token_hash: str,
        now: datetime,
    ) -> TokenResolution: ...

    def revoke_token(self, *, token_hash: str, now: datetime) -> None: ...
