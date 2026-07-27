from __future__ import annotations

from uuid import UUID

from kefe_api.modules.context.models import ContextSnapshot


class InMemoryContextRepository:
    def __init__(self, snapshots: list[ContextSnapshot]) -> None:
        self._snapshots = {snapshot.case_version_id: snapshot for snapshot in snapshots}

    def get_context(self, case_version_id: UUID) -> ContextSnapshot | None:
        return self._snapshots.get(case_version_id)
