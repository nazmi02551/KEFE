from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from kefe_api.modules.decision.models import CaseVersion, RevealSnapshot, WeighSession


class InMemoryDecisionRepository:
    def __init__(self, *, cases: list[CaseVersion], reveals: list[RevealSnapshot]) -> None:
        self._cases = {case.id: case for case in cases}
        self._current_by_case = {case.case_id: case.id for case in cases}
        self._sessions: dict[UUID, WeighSession] = {}
        self._reveals = {snapshot.case_version_id: snapshot for snapshot in reveals}
        self.events: list[dict[str, Any]] = []

    def get_current_case_version(self, case_id: UUID) -> CaseVersion | None:
        version_id = self._current_by_case.get(case_id)
        return self._cases.get(version_id) if version_id else None

    def get_case_version(self, version_id: UUID) -> CaseVersion | None:
        return self._cases.get(version_id)

    def save_session(self, session: WeighSession) -> None:
        self._sessions[session.id] = deepcopy(session)

    def get_session(self, session_id: UUID) -> WeighSession | None:
        session = self._sessions.get(session_id)
        return deepcopy(session) if session else None

    def get_reveal(self, case_version_id: UUID) -> RevealSnapshot | None:
        return self._reveals.get(case_version_id)

    def append_event(self, name: str, aggregate_id: UUID, payload: dict[str, object]) -> None:
        self.events.append(
            {
                "name": name,
                "aggregate_id": str(aggregate_id),
                "payload": payload,
                "occurred_at": datetime.now(UTC).isoformat(),
            }
        )
