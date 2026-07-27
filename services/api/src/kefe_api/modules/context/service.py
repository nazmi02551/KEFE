from __future__ import annotations

from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.context.ports import ContextRepository


class ContextService:
    def __init__(self, repository: ContextRepository) -> None:
        self._repository = repository

    def get_context(self, case_version_id: UUID):
        snapshot = self._repository.get_context(case_version_id)
        if snapshot is None:
            raise DomainError(
                "CASE_VERSION_CONTEXT_NOT_FOUND",
                "Context not found for CaseVersion",
                404,
            )
        return snapshot
