from __future__ import annotations

from uuid import UUID

from kefe_api.modules.progress.models import DecisionJourneySnapshot, ProgressSnapshot
from kefe_api.modules.progress.ports import ProgressRepository


class ProgressService:
    def __init__(self, repository: ProgressRepository) -> None:
        self._repository = repository

    def get_progress(self, actor_id: UUID) -> ProgressSnapshot:
        return self._repository.get_progress(actor_id, recent_limit=5)

    def get_journey(self, actor_id: UUID) -> DecisionJourneySnapshot:
        return self._repository.get_journey(
            actor_id,
            recent_limit=5,
            domain_limit=12,
        )
