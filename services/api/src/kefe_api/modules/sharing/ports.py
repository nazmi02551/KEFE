from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.sharing.models import ShareRecord


class ShareRepository(Protocol):
    def create(self, record: ShareRecord) -> None: ...

    def get_by_token_hash(self, token_hash: str) -> ShareRecord | None: ...

    def revoke(self, *, share_id: UUID, actor_id: UUID, revoked_at: datetime) -> bool: ...
