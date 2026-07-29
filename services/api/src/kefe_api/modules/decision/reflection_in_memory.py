from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from kefe_api.modules.decision.lineage_in_memory import InMemoryLineageDecisionRepository
from kefe_api.modules.decision.reflection_models import (
    ReflectionCompletion,
    ReflectionCompletionAttempt,
    ReflectionCompletionStatus,
)


class InMemoryReflectionDecisionRepository(InMemoryLineageDecisionRepository):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._reflection_completions: dict[UUID, list[ReflectionCompletion]] = {}

    def list_reflection_completions(
        self, session_id: UUID
    ) -> tuple[ReflectionCompletion, ...]:
        with self._lock:
            return tuple(self._reflection_completions.get(session_id, ()))

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
        with self._lock:
            session = self._sessions.get(session_id)
            if (
                session is None
                or session.actor_id != actor_id
                or session.case_version_id != case_version_id
            ):
                raise ValueError("session ownership mismatch")

            completions = self._reflection_completions.setdefault(session_id, [])
            for item in completions:
                if item.idempotency_key == idempotency_key:
                    if (
                        item.flow_step_code == flow_step_code
                        and item.latest_revision_id == latest_revision_id
                    ):
                        return ReflectionCompletionAttempt(
                            ReflectionCompletionStatus.IDEMPOTENT_REPLAY, item
                        )
                    return ReflectionCompletionAttempt(
                        ReflectionCompletionStatus.IDEMPOTENCY_KEY_REUSED, None
                    )

            existing = next(
                (
                    item
                    for item in completions
                    if item.flow_step_code == flow_step_code
                    and item.latest_revision_id == latest_revision_id
                ),
                None,
            )
            if existing is not None:
                return ReflectionCompletionAttempt(
                    ReflectionCompletionStatus.ALREADY_COMPLETED, existing
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
            completions.append(completion)
            self._append_event(
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
                ReflectionCompletionStatus.COMPLETED, completion
            )
