from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import text

from kefe_api.infrastructure.postgres_decision_lineage import PostgresDecisionLineageRepository
from kefe_api.modules.decision.reflection_models import (
    ReflectionCompletion,
    ReflectionCompletionAttempt,
    ReflectionCompletionStatus,
)


class PostgresReflectionDecisionRepository(PostgresDecisionLineageRepository):
    """Decision lineage adapter extended with immutable Reflection completions."""

    def list_reflection_completions(
        self, session_id: UUID
    ) -> tuple[ReflectionCompletion, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                        SELECT * FROM decision.reflection_completion
                        WHERE session_id = :session_id
                        ORDER BY completed_at, id
                        """
                    ),
                    {"session_id": session_id},
                )
                .mappings()
                .all()
            )
        return tuple(self._completion_from_row(row) for row in rows)

    def complete_reflection(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        case_version_id: UUID,
        flow_step_code: str,
        latest_revision_id: UUID,
        latest_delta_id: UUID | None,
        idempotency_key: str,
        completed_at: datetime,
    ) -> ReflectionCompletionAttempt:
        with self._engine.begin() as connection:
            session_row = self._lock_session(
                connection,
                actor_id=actor_id,
                session_id=session_id,
            )
            if session_row is None or session_row["case_version_id"] != case_version_id:
                raise ValueError("session ownership mismatch")

            replay_row = (
                connection.execute(
                    text(
                        """
                        SELECT * FROM decision.reflection_completion
                        WHERE session_id = :session_id
                          AND idempotency_key = :idempotency_key
                        """
                    ),
                    {"session_id": session_id, "idempotency_key": idempotency_key},
                )
                .mappings()
                .one_or_none()
            )
            if replay_row is not None:
                replay = self._completion_from_row(replay_row)
                if (
                    replay.flow_step_code == flow_step_code
                    and replay.latest_revision_id == latest_revision_id
                ):
                    return ReflectionCompletionAttempt(
                        ReflectionCompletionStatus.IDEMPOTENT_REPLAY,
                        replay,
                    )
                return ReflectionCompletionAttempt(
                    ReflectionCompletionStatus.IDEMPOTENCY_KEY_REUSED,
                    None,
                )

            current_row = (
                connection.execute(
                    text(
                        """
                        SELECT * FROM decision.reflection_completion
                        WHERE session_id = :session_id
                          AND flow_step_code = :flow_step_code
                          AND latest_revision_id = :latest_revision_id
                        """
                    ),
                    {
                        "session_id": session_id,
                        "flow_step_code": flow_step_code,
                        "latest_revision_id": latest_revision_id,
                    },
                )
                .mappings()
                .one_or_none()
            )
            if current_row is not None:
                return ReflectionCompletionAttempt(
                    ReflectionCompletionStatus.ALREADY_COMPLETED,
                    self._completion_from_row(current_row),
                )

            completion = ReflectionCompletion(
                id=uuid4(),
                session_id=session_id,
                actor_id=actor_id,
                case_version_id=case_version_id,
                flow_step_code=flow_step_code,
                latest_revision_id=latest_revision_id,
                latest_delta_id=latest_delta_id,
                idempotency_key=idempotency_key,
                completed_at=completed_at,
            )
            connection.execute(
                text(
                    """
                    INSERT INTO decision.reflection_completion (
                        id, session_id, actor_id, case_version_id, flow_step_code,
                        latest_revision_id, latest_delta_id, idempotency_key, completed_at
                    ) VALUES (
                        :id, :session_id, :actor_id, :case_version_id, :flow_step_code,
                        :latest_revision_id, :latest_delta_id, :idempotency_key, :completed_at
                    )
                    """
                ),
                {
                    "id": completion.id,
                    "session_id": completion.session_id,
                    "actor_id": completion.actor_id,
                    "case_version_id": completion.case_version_id,
                    "flow_step_code": completion.flow_step_code,
                    "latest_revision_id": completion.latest_revision_id,
                    "latest_delta_id": completion.latest_delta_id,
                    "idempotency_key": completion.idempotency_key,
                    "completed_at": completion.completed_at,
                },
            )
            self._append_event(
                connection,
                "reflection.completed",
                session_id,
                {
                    "reflection_completion_id": str(completion.id),
                    "flow_step_code": flow_step_code,
                    "latest_revision_id": str(latest_revision_id),
                    "latest_delta_id": str(latest_delta_id) if latest_delta_id else None,
                },
            )
            return ReflectionCompletionAttempt(
                ReflectionCompletionStatus.COMPLETED,
                completion,
            )

    @staticmethod
    def _completion_from_row(row) -> ReflectionCompletion:
        return ReflectionCompletion(
            id=row["id"],
            session_id=row["session_id"],
            actor_id=row["actor_id"],
            case_version_id=row["case_version_id"],
            flow_step_code=row["flow_step_code"],
            latest_revision_id=row["latest_revision_id"],
            latest_delta_id=row["latest_delta_id"],
            idempotency_key=row["idempotency_key"],
            completed_at=row["completed_at"],
        )
