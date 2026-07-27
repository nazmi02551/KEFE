from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import UUID

from kefe_api.modules.decision.models import (
    CaseVersion,
    CommitAttempt,
    CommitStatus,
    DraftUpdateAttempt,
    DraftUpdateStatus,
    RevealSnapshot,
    WeighSession,
    WeighState,
)


class InMemoryDecisionRepository:
    def __init__(self, *, cases: list[CaseVersion], reveals: list[RevealSnapshot]) -> None:
        self._cases = {case.id: case for case in cases}
        self._current_by_case = {case.case_id: case.id for case in cases}
        self._sessions: dict[UUID, WeighSession] = {}
        self._reveals = {snapshot.case_version_id: snapshot for snapshot in reveals}
        self.events: list[dict[str, Any]] = []
        self._lock = RLock()

    def get_current_case_version(self, case_id: UUID) -> CaseVersion | None:
        with self._lock:
            version_id = self._current_by_case.get(case_id)
            return self._cases.get(version_id) if version_id else None

    def get_case_version(self, version_id: UUID) -> CaseVersion | None:
        with self._lock:
            return self._cases.get(version_id)

    def save_session_with_event(
        self,
        session: WeighSession,
        *,
        event_name: str,
        payload: dict[str, object],
    ) -> None:
        with self._lock:
            self._sessions[session.id] = deepcopy(session)
            self._append_event(event_name, session.id, payload)

    def get_session(self, session_id: UUID) -> WeighSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            return deepcopy(session) if session else None

    def update_draft_responses(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        responses: dict[UUID, Any],
    ) -> DraftUpdateAttempt:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.actor_id != actor_id:
                return DraftUpdateAttempt(DraftUpdateStatus.NOT_FOUND, None)
            if session.state is not WeighState.DRAFT:
                return DraftUpdateAttempt(DraftUpdateStatus.NOT_EDITABLE, deepcopy(session))
            session.responses.update(responses)
            return DraftUpdateAttempt(DraftUpdateStatus.UPDATED, deepcopy(session))

    def commit_session(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        idempotency_key: str,
        required_question_ids: frozenset[UUID],
        committed_at: datetime,
    ) -> CommitAttempt:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.actor_id != actor_id:
                return CommitAttempt(CommitStatus.NOT_FOUND, None)

            for other in self._sessions.values():
                if (
                    other.id != session_id
                    and other.actor_id == actor_id
                    and other.commit_key == idempotency_key
                ):
                    return CommitAttempt(CommitStatus.IDEMPOTENCY_KEY_REUSED, deepcopy(session))

            if session.state is WeighState.COMMITTED:
                status = (
                    CommitStatus.IDEMPOTENT_REPLAY
                    if session.commit_key == idempotency_key
                    else CommitStatus.ALREADY_COMMITTED
                )
                return CommitAttempt(status, deepcopy(session))

            current_id = self._current_by_case.get(session.case_id)
            current = self._cases.get(current_id) if current_id else None
            if (
                session.state is not WeighState.DRAFT
                or current is None
                or current.id != session.case_version_id
                or not current.accepts_weighs
            ):
                session.state = WeighState.BLOCKED_BY_VERSION
                return CommitAttempt(CommitStatus.STALE_VERSION, deepcopy(session))

            missing = tuple(sorted(required_question_ids - session.responses.keys(), key=str))
            if missing:
                return CommitAttempt(CommitStatus.INCOMPLETE, deepcopy(session), missing)

            session.state = WeighState.COMMITTED
            session.commit_key = idempotency_key
            session.committed_at = committed_at
            self._append_event(
                "weigh.committed",
                session.id,
                {
                    "actor_id": str(actor_id),
                    "case_version_id": str(session.case_version_id),
                    "committed_at": committed_at.isoformat(),
                },
            )
            return CommitAttempt(CommitStatus.COMMITTED, deepcopy(session))

    def get_reveal(self, case_version_id: UUID) -> RevealSnapshot | None:
        with self._lock:
            return self._reveals.get(case_version_id)

    def append_event(self, name: str, aggregate_id: UUID, payload: dict[str, object]) -> None:
        with self._lock:
            self._append_event(name, aggregate_id, payload)

    def _append_event(
        self,
        name: str,
        aggregate_id: UUID,
        payload: dict[str, object],
    ) -> None:
        self.events.append(
            {
                "name": name,
                "aggregate_id": str(aggregate_id),
                "payload": payload,
                "occurred_at": datetime.now(UTC).isoformat(),
            }
        )
