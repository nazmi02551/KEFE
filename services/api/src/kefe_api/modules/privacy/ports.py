from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.privacy.models import PrivacyDeletionReceipt


class PrivacyRepository(Protocol):
    def export_actor_data(self, actor_id: UUID) -> dict[str, object]: ...

    def delete_actor_data(
        self,
        *,
        actor_id: UUID,
        actor_kind: str,
        deleted_at: datetime,
    ) -> PrivacyDeletionReceipt: ...
