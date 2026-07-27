from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.context.models import ContextSnapshot


class ContextRepository(Protocol):
    def get_context(self, case_version_id: UUID) -> ContextSnapshot | None: ...
