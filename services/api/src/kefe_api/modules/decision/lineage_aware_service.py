from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from kefe_api.modules.decision.service import DecisionService


class LineageAwareDecisionService(DecisionService):
    """Existing Decision behavior plus server-observed gated delivery exposures."""

    def reveal(self, *, actor_id: UUID, session_id: UUID):
        snapshot = super().reveal(actor_id=actor_id, session_id=session_id)
        session = self._committed_owned_session(actor_id, session_id)
        case = self._repo.get_case_version(session.case_version_id)
        step = self._result_step(case)
        self._repo.record_exposure(
            actor_id=actor_id,
            session_id=session_id,
            case_version_id=session.case_version_id,
            flow_step_code=step[0],
            resource_category="COLLECTIVE_RESULT",
            resource_ref=None,
            primitive_code="COLLECTIVE_RESULT",
            capability_codes=step[1],
            metadata={"layer": snapshot.layer, "delivery": "REVEAL_ENDPOINT"},
            idempotency_key=f"server:reveal:{uuid4()}",
            occurred_at=datetime.now(UTC),
        )
        return snapshot

    def perspectives(self, *, actor_id: UUID, session_id: UUID):
        snapshot = super().perspectives(actor_id=actor_id, session_id=session_id)
        session = self._committed_owned_session(actor_id, session_id)
        case = self._repo.get_case_version(session.case_version_id)
        step = self._result_step(case)
        self._repo.record_exposure(
            actor_id=actor_id,
            session_id=session_id,
            case_version_id=session.case_version_id,
            flow_step_code=step[0],
            resource_category="PERSPECTIVE",
            resource_ref=None,
            primitive_code="COLLECTIVE_RESULT",
            capability_codes=step[1],
            metadata={
                "mode": snapshot.mode.value,
                "card_count": len(snapshot.cards),
                "delivery": "PERSPECTIVE_ENDPOINT",
            },
            idempotency_key=f"server:perspective:{uuid4()}",
            occurred_at=datetime.now(UTC),
        )
        return snapshot

    @staticmethod
    def _result_step(case) -> tuple[str, tuple[str, ...]]:
        if case is not None and case.resolved_flow is not None:
            step = next(
                (
                    item
                    for item in case.resolved_flow.steps
                    if item.primitive_code == "COLLECTIVE_RESULT"
                ),
                None,
            )
            if step is not None:
                return step.code, step.capability_codes
        return "RESULT", ()
