from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.decision.models import CommitAttempt


class InMemoryLineageDecisionRepository(InMemoryDecisionRepository):
    """Compatibility adapter that derives the initial Decision Step from the pinned Flow."""

    def commit_session(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        idempotency_key: str,
        required_question_ids: frozenset[UUID],
        committed_at: datetime,
        flow_step_code: str | None = None,
    ) -> CommitAttempt:
        if flow_step_code is None:
            session = self.get_session(session_id)
            case = self.get_case_version(session.case_version_id) if session else None
            flow_step_code = "INITIAL_DECISION"
            if case is not None and case.resolved_flow is not None:
                flow_step_code = next(
                    (
                        step.code
                        for step in case.resolved_flow.steps
                        if step.primitive_code == "DECISION"
                    ),
                    flow_step_code,
                )
        return super().commit_session(
            actor_id=actor_id,
            session_id=session_id,
            idempotency_key=idempotency_key,
            required_question_ids=required_question_ids,
            flow_step_code=flow_step_code,
            committed_at=committed_at,
        )
