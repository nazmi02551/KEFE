from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.progress.models import DecisionJourneySnapshot, ProgressSnapshot


class ProgressRepository(Protocol):
    def get_progress(self, actor_id: UUID, *, recent_limit: int) -> ProgressSnapshot: ...

    def get_journey(
        self,
        actor_id: UUID,
        *,
        recent_limit: int,
        domain_limit: int,
    ) -> DecisionJourneySnapshot: ...
