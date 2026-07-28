from __future__ import annotations

from uuid import UUID

from kefe_api.modules.progress.ports import ProgressRepository


class ProgressService:
    def __init__(self, repository: ProgressRepository) -> None:
        self._repository = repository

    def get_progress(self, actor_id: UUID):
        return self._repository.get_progress(actor_id, recent_limit=5)
