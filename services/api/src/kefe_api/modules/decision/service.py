from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.decision.models import (
    CommitStatus,
    DraftUpdateStatus,
    PerspectiveSelection,
    PrivateReason,
    Question,
    WeighSession,
    WeighState,
)
from kefe_api.modules.decision.ports import DecisionRepository

PERSPECTIVE_SELECTION_POLICY = "EDITORIAL_OPPOSITION_V1"
PERSPECTIVE_TECHNICAL_LIMIT = 10


class DecisionService:
    def __init__(self, repository: DecisionRepository) -> None:
        self._repo = repository

    def list_cases(self, *, limit: int = 20):
        bounded_limit = min(max(limit, 1), 50)
        return self._repo.list_current_cases(limit=bounded_limit)

    def get_case(self, case_id: UUID):
        case = self._repo.get_current_case_version(case_id)
        if case is None:
            raise DomainError("CASE_NOT_FOUND", "Case not found", 404)
        return case

    def start_session(self, *, actor_id: UUID, case_id: UUID) -> WeighSession:
        case = self.get_case(case_id)
        if not case.accepts_weighs:
            raise DomainError(
                "CASE_NOT_ACCEPTING_WEIGHS",
                "Case is not accepting weighs",
                409,
            )
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
        case = self._repo.get_case_version(session.case_version_id)
        if case is None:
            raise DomainError("CASE_VERSION_STALE", "Case version is no longer available", 409)

        questions = {question.id: question for question in case.questions}
        unknown = [str(question_id) for question_id in responses if question_id not in questions]
        if unknown:
            raise DomainError(
                "WEIGH_RESPONSE_INVALID",
                "Response contains unknown questions",
                422,
                meta={"unknown_question_ids": unknown},
            )

        invalid = [
            {
                "question_id": str(question_id),
                "response_type": questions[question_id].response_type,
            }
            for question_id, value in responses.items()
            if not self._is_valid_response(questions[question_id], value)
        ]
        if invalid:
            raise DomainError(
                "WEIGH_RESPONSE_INVALID",
                "Response does not match the question schema",
                422,
                meta={"invalid_responses": invalid},
            )

        attempt = self._repo.update_draft_responses(
            actor_id=actor_id,
            session_id=session_id,
            responses=responses,
        )
        if attempt.status is DraftUpdateStatus.NOT_FOUND:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        if attempt.status is DraftUpdateStatus.NOT_EDITABLE:
            raise DomainError(
                "WEIGH_SESSION_NOT_EDITABLE",
                "Weigh session is not editable",
                409,
            )
        assert attempt.session is not None
        return attempt.session

    def update_private_reason(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        tags: list[str],
        text: str | None,
    ) -> PrivateReason:
        session = self._owned_session(actor_id, session_id)
        case = self._repo.get_case_version(session.case_version_id)
        if case is None:
            raise DomainError("CASE_VERSION_STALE", "Case version is no longer available", 409)

        policy = self._reason_policy(case.questions)
        if policy is None:
            raise DomainError(
                "REASON_NOT_SUPPORTED",
                "This Case does not accept a structured reason",
                422,
            )

        normalized_tags = tuple(dict.fromkeys(tag.strip().upper() for tag in tags if tag.strip()))
        normalized_text = text.strip() if text is not None else None
        if normalized_text == "":
            normalized_text = None
        if not normalized_tags and normalized_text is None:
            raise DomainError(
                "REASON_EMPTY",
                "At least one reason tag or short text is required",
                422,
            )

        allowed_tags = {
            str(tag).strip().upper()
            for tag in policy.get("tags", ())
            if str(tag).strip()
        }
        unknown_tags = [tag for tag in normalized_tags if tag not in allowed_tags]
        if unknown_tags:
            raise DomainError(
                "REASON_TAG_INVALID",
                "Reason contains unsupported tags",
                422,
                meta={"unknown_tags": unknown_tags},
            )

        max_tags = self._bounded_int(policy.get("max_tags", 3), default=3, minimum=1, maximum=10)
        if len(normalized_tags) > max_tags:
            raise DomainError(
                "REASON_TAG_LIMIT_EXCEEDED",
                "Too many reason tags",
                422,
                meta={"max_tags": max_tags},
            )

        text_enabled = policy.get("text_enabled", False) is True
        if normalized_text is not None and not text_enabled:
            raise DomainError(
                "REASON_TEXT_NOT_ALLOWED",
                "Short reason text is disabled for this Case",
                422,
            )
        text_max_length = self._bounded_int(
            policy.get("text_max_length", 500),
            default=500,
            minimum=1,
            maximum=1000,
        )
        if normalized_text is not None and len(normalized_text) > text_max_length:
            raise DomainError(
                "REASON_TEXT_TOO_LONG",
                "Short reason text exceeds the Case limit",
                422,
                meta={"max_length": text_max_length},
            )

        attempt = self._repo.update_private_reason(
            actor_id=actor_id,
            session_id=session_id,
            tags=normalized_tags,
            text=normalized_text,
            updated_at=datetime.now(UTC),
        )
        if attempt.status is DraftUpdateStatus.NOT_FOUND:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        if attempt.status is DraftUpdateStatus.NOT_EDITABLE:
            raise DomainError(
                "WEIGH_SESSION_NOT_EDITABLE",
                "Reason cannot be changed after Commit",
                409,
            )
        assert attempt.reason is not None
        return attempt.reason

    def commit(self, *, actor_id: UUID, session_id: UUID, idempotency_key: str) -> WeighSession:
        session = self._owned_session(actor_id, session_id)
        pinned = self._repo.get_case_version(session.case_version_id)
        if pinned is None:
            raise DomainError("CASE_VERSION_STALE", "Case version is no longer available", 409)

        attempt = self._repo.commit_session(
            actor_id=actor_id,
            session_id=session_id,
            idempotency_key=idempotency_key,
            required_question_ids=frozenset(
                question.id for question in pinned.questions if question.required
            ),
            committed_at=datetime.now(UTC),
        )

        if attempt.status in {CommitStatus.COMMITTED, CommitStatus.IDEMPOTENT_REPLAY}:
            assert attempt.session is not None
            return attempt.session
        if attempt.status is CommitStatus.NOT_FOUND:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        if attempt.status is CommitStatus.ALREADY_COMMITTED:
            raise DomainError(
                "WEIGH_SESSION_ALREADY_COMMITTED",
                "Weigh session is already committed",
                409,
            )
        if attempt.status is CommitStatus.STALE_VERSION:
            raise DomainError(
                "CASE_VERSION_STALE",
                "Case version changed before commit",
                409,
                meta={"session_case_version_id": str(session.case_version_id)},
            )
        if attempt.status is CommitStatus.INCOMPLETE:
            raise DomainError(
                "WEIGH_RESPONSE_INCOMPLETE",
                "Required responses are missing",
                422,
                meta={
                    "missing_question_ids": [
                        str(question_id) for question_id in attempt.missing_question_ids
                    ]
                },
            )
        if attempt.status is CommitStatus.IDEMPOTENCY_KEY_REUSED:
            raise DomainError(
                "IDEMPOTENCY_KEY_REUSED",
                "Idempotency key was already used for another commit",
                409,
            )
        raise RuntimeError(f"Unsupported commit status: {attempt.status}")

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

    def perspectives(self, *, actor_id: UUID, session_id: UUID) -> PerspectiveSelection:
        session = self._owned_session(actor_id, session_id)
        if session.state is not WeighState.COMMITTED:
            raise DomainError(
                "PERSPECTIVE_COMMIT_REQUIRED",
                "Commit is required before perspectives are available",
                403,
            )

        case = self._repo.get_case_version(session.case_version_id)
        if case is None:
            raise DomainError("CASE_VERSION_STALE", "Case version is no longer available", 409)

        axis = next(
            (
                question
                for question in case.questions
                if question.response_type == "SINGLE_CHOICE"
                and question.id in session.responses
            ),
            None,
        )
        if axis is None:
            return PerspectiveSelection(
                question_version_id=None,
                viewer_value=None,
                selection_policy=PERSPECTIVE_SELECTION_POLICY,
                items=(),
            )

        viewer_value = session.responses[axis.id]
        items = self._repo.get_opposing_perspectives(
            case_version_id=session.case_version_id,
            question_version_id=axis.id,
            viewer_value=viewer_value,
            limit=PERSPECTIVE_TECHNICAL_LIMIT,
        )
        return PerspectiveSelection(
            question_version_id=axis.id,
            viewer_value=viewer_value,
            selection_policy=PERSPECTIVE_SELECTION_POLICY,
            items=items,
        )

    def _owned_session(self, actor_id: UUID, session_id: UUID) -> WeighSession:
        session = self._repo.get_session(session_id)
        if session is None or session.actor_id != actor_id:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        return session

    @staticmethod
    def _reason_policy(questions: tuple[Question, ...]) -> Mapping[str, Any] | None:
        for question in questions:
            raw = question.response_schema.get("reason")
            if isinstance(raw, Mapping):
                return raw
        return None

    @staticmethod
    def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            return default
        return min(max(value, minimum), maximum)

    @staticmethod
    def _is_valid_response(question: Question, value: Any) -> bool:
        if question.response_type == "SINGLE_CHOICE":
            return isinstance(value, str) and value in question.options

        if question.response_type == "CONFIDENCE":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return False
            minimum = question.response_schema.get("min", 1)
            maximum = question.response_schema.get("max", 5)
            step = question.response_schema.get("step", 1)
            if not all(isinstance(item, (int, float)) for item in (minimum, maximum, step)):
                return False
            if step <= 0 or value < minimum or value > maximum:
                return False
            steps = (value - minimum) / step
            return abs(steps - round(steps)) < 1e-9

        return False
