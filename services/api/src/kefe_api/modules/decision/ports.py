from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.decision.models import CaseVersion, RevealSnapshot, WeighSession


class DecisionRepository(Protocol):
    def get_current_case_version(self, case_id: UUID) -> CaseVersion | None: ...

    def get_case_version(self, version_id: UUID) -> CaseVersion | None: ...

    def save_session(self, session: WeighSession) -> None: ...

    def save_session_with_event(
        self,
        session: WeighSession,
        *,
        event_name: str,
        payload: dict[str, object],
    ) -> None: ...

    def get_session(self, session_id: UUID) -> WeighSession | None: ...

    def get_reveal(self, case_version_id: UUID) -> RevealSnapshot | None: ...

    def append_event(self, name: str, aggregate_id: UUID, payload: dict[str, object]) -> None: ...
