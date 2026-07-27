from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.decision.models import WeighSession, WeighState
from kefe_api.modules.decision.ports import DecisionRepository


class DecisionService:
    def __init__(self, repository: DecisionRepository) -> None:
        self._repo = repository

    def get_case(self, case_id: UUID):
        case = self._repo.get_current_case_version(case_id)
        if case is None:
            raise DomainError("CASE_NOT_FOUND", "Case not found", 404)
        return case

    def start_session(self, *, actor_id: UUID, case_id: UUID) -> WeighSession:
        case = self.get_case(case_id)
        if not case.accepts_weighs:
            raise DomainError("CASE_VERSION_CLOSED", "Case is not accepting weighs", 409)
        session = WeighSession(
            id=uuid4(),
            actor_id=actor_id,
            case_id=case.case_id,
            case_version_id=case.id,
        )
        self._repo.save_session_with_event(
            session,
            event_name="weigh.started",
            payload={"actor_id": str(actor_id), "case_version_id": str(case.id)},
        )
        return session

    def update_responses(
        self, *, actor_id: UUID, session_id: UUID, responses: dict[UUID, Any]
    ) -> WeighSession:
        session = self._owned_session(actor_id, session_id)
        if session.state is not WeighState.DRAFT:
            raise DomainError("WEIGH_SESSION_NOT_EDITABLE", "Weigh session is not editable", 409)

        case = self._repo.get_case_version(session.case_version_id)
        if case is None:
            raise DomainError("CASE_VERSION_NOT_FOUND", "Case version not found", 409)
        allowed = {question.id for question in case.questions}
        unknown = [str(question_id) for question_id in responses if question_id not in allowed]
        if unknown:
            raise DomainError(
                "WEIGH_RESPONSE_INVALID",
                "Response contains unknown questions",
                422,
                meta={"unknown_question_ids": unknown},
            )
        session.responses.update(responses)
        self._repo.save_session(session)
        return session

    def commit(self, *, actor_id: UUID, session_id: UUID, idempotency_key: str) -> WeighSession:
        session = self._owned_session(actor_id, session_id)

        if session.state is WeighState.COMMITTED:
            if session.commit_key == idempotency_key:
                return session
            raise DomainError(
                "WEIGH_SESSION_ALREADY_COMMITTED",
                "Weigh session is already committed",
                409,
            )

        current = self._repo.get_current_case_version(session.case_id)
        if current is None or current.id != session.case_version_id or not current.accepts_weighs:
            session.state = WeighState.BLOCKED_BY_VERSION
            self._repo.save_session(session)
            raise DomainError(
                "CASE_VERSION_STALE",
                "Case version changed before commit",
                409,
                meta={"session_case_version_id": str(session.case_version_id)},
            )

        required = {question.id for question in current.questions}
        missing = [str(question_id) for question_id in required - session.responses.keys()]
        if missing:
            raise DomainError(
                "WEIGH_RESPONSE_INCOMPLETE",
                "Required responses are missing",
                422,
                meta={"missing_question_ids": missing},
            )

        session.state = WeighState.COMMITTED
        session.commit_key = idempotency_key
        session.committed_at = datetime.now(UTC)
        self._repo.save_session_with_event(
            session,
            event_name="weigh.committed",
            payload={
                "actor_id": str(actor_id),
                "case_version_id": str(session.case_version_id),
                "committed_at": session.committed_at.isoformat(),
            },
        )
        return session

    def reveal(self, *, actor_id: UUID, session_id: UUID):
        session = self._owned_session(actor_id, session_id)
        if session.state is not WeighState.COMMITTED:
            raise DomainError(
                "RESULT_COMMIT_REQUIRED",
                "Commit is required before reveal",
                403,
            )
        snapshot = self._repo.get_reveal(session.case_version_id)
        if snapshot is None:
            raise DomainError(
                "RESULT_NOT_READY",
                "Trusted result is not ready",
                409,
                retryable=True,
            )
        self._repo.append_event(
            "result.revealed",
            session.id,
            {"case_version_id": str(session.case_version_id), "layer": snapshot.layer},
        )
        return snapshot

    def _owned_session(self, actor_id: UUID, session_id: UUID) -> WeighSession:
        session = self._repo.get_session(session_id)
        if session is None or session.actor_id != actor_id:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        return session
