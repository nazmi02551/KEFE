from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.decision.models import CaseVersion, FlowStep
from kefe_api.modules.decision.ports import DecisionRepository
from kefe_api.modules.decision.reflection_models import (
    ReflectionCompletion,
    ReflectionCompletionStatus,
    ReflectionReadModel,
)
from kefe_api.modules.flow_runtime.models import FlowStepRuntimeState
from kefe_api.modules.flow_runtime.service import FlowRuntimeService


class ReflectionService:
    def __init__(
        self,
        repository: DecisionRepository,
        flow_runtime: FlowRuntimeService,
    ) -> None:
        self._repo = repository
        self._flow_runtime = flow_runtime

    def read(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        flow_step_code: str,
    ) -> ReflectionReadModel:
        session = self._owned_session(actor_id, session_id)
        case = self._case(session.case_version_id)
        self._reflection_step(case, flow_step_code)
        runtime_step = self._runtime_step(actor_id, session_id, flow_step_code)
        if runtime_step.state not in {
            FlowStepRuntimeState.READY,
            FlowStepRuntimeState.COMPLETED,
        }:
            raise DomainError(
                "FLOW_STEP_NOT_READY",
                "Reflection Flow Step is not ready",
                409,
                meta={"state": runtime_step.state.value},
            )

        revisions = self._repo.list_decision_revisions(session_id)
        if not revisions:
            raise DomainError(
                "REFLECTION_REVISION_REQUIRED",
                "Reflection requires a committed DecisionRevision",
                409,
            )
        latest = revisions[-1]
        deltas = self._repo.list_decision_deltas(session_id)
        latest_delta = next(
            (item for item in reversed(deltas) if item.to_revision_id == latest.id),
            None,
        )
        interventions = self._repo.list_interventions(session_id)
        intervention_by_id = {item.id: item for item in interventions}
        related = (
            tuple(
                intervention_by_id[item_id]
                for item_id in latest_delta.intervention_ids
                if item_id in intervention_by_id
            )
            if latest_delta is not None
            else ()
        )
        previous = None
        if latest_delta is not None:
            previous = next(
                (item for item in revisions if item.id == latest_delta.from_revision_id),
                None,
            )
        changed_count = (
            int(latest_delta.diff_snapshot.get("changed_count", 0))
            if latest_delta is not None
            else 0
        )
        completions = self._repo.list_reflection_completions(session_id)
        completed = any(
            item.flow_step_code == flow_step_code
            and item.latest_revision_id == latest.id
            for item in completions
        )
        return ReflectionReadModel(
            session_id=session_id,
            case_version_id=session.case_version_id,
            flow_step_code=flow_step_code,
            revision_count=len(revisions),
            latest_revision_id=latest.id,
            latest_delta_id=latest_delta.id if latest_delta else None,
            decision_changed=changed_count > 0,
            changed_question_count=changed_count,
            intervention_count=len(related),
            intervention_type_codes=tuple(dict.fromkeys(item.type_code for item in related)),
            from_contribution_class=(
                previous.contribution_class.value if previous is not None else None
            ),
            to_contribution_class=latest.contribution_class.value,
            completed=completed,
        )

    def complete(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        flow_step_code: str,
        idempotency_key: str,
    ) -> ReflectionCompletion:
        model = self.read(
            actor_id=actor_id,
            session_id=session_id,
            flow_step_code=flow_step_code,
        )
        attempt = self._repo.complete_reflection(
            actor_id=actor_id,
            session_id=session_id,
            case_version_id=model.case_version_id,
            flow_step_code=flow_step_code,
            latest_revision_id=model.latest_revision_id,
            latest_delta_id=model.latest_delta_id,
            idempotency_key=idempotency_key,
            completed_at=datetime.now(UTC),
        )
        if attempt.status in {
            ReflectionCompletionStatus.COMPLETED,
            ReflectionCompletionStatus.IDEMPOTENT_REPLAY,
        }:
            assert attempt.completion is not None
            return attempt.completion
        if attempt.status is ReflectionCompletionStatus.ALREADY_COMPLETED:
            raise DomainError(
                "REFLECTION_ALREADY_COMPLETED",
                "Reflection is already completed for the current DecisionRevision",
                409,
            )
        if attempt.status is ReflectionCompletionStatus.IDEMPOTENCY_KEY_REUSED:
            raise DomainError(
                "IDEMPOTENCY_KEY_REUSED",
                "Idempotency key was already used for another Reflection completion",
                409,
            )
        raise RuntimeError(f"Unsupported Reflection completion status: {attempt.status}")

    def _owned_session(self, actor_id: UUID, session_id: UUID):
        session = self._repo.get_session(session_id)
        if session is None or session.actor_id != actor_id:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        return session

    def _case(self, case_version_id: UUID) -> CaseVersion:
        case = self._repo.get_case_version(case_version_id)
        if case is None:
            raise DomainError("CASE_VERSION_STALE", "Case version is no longer available", 409)
        if case.resolved_flow is None:
            raise DomainError(
                "FLOW_RUNTIME_UNAVAILABLE",
                "CaseVersion does not contain a pinned resolved Flow",
                409,
            )
        return case

    @staticmethod
    def _reflection_step(case: CaseVersion, flow_step_code: str) -> FlowStep:
        assert case.resolved_flow is not None
        step = next(
            (item for item in case.resolved_flow.steps if item.code == flow_step_code),
            None,
        )
        if step is None:
            raise DomainError("FLOW_STEP_NOT_FOUND", "Flow Step not found", 404)
        if step.primitive_code != "REFLECTION":
            raise DomainError(
                "REFLECTION_STEP_INVALID",
                "Requested Flow Step is not a Reflection Step",
                422,
            )
        return step

    def _runtime_step(self, actor_id: UUID, session_id: UUID, flow_step_code: str):
        runtime = self._flow_runtime.get_runtime(
            actor_id=actor_id,
            session_id=session_id,
        )
        step = next((item for item in runtime.steps if item.code == flow_step_code), None)
        if step is None:
            raise DomainError("FLOW_STEP_NOT_FOUND", "Flow Step not found", 404)
        return step
