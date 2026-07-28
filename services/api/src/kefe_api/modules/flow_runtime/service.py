from __future__ import annotations

from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.decision.models import FlowStep, ResolvedFlow, WeighState
from kefe_api.modules.decision.ports import DecisionRepository
from kefe_api.modules.flow_runtime.models import (
    FlowExecutionSupport,
    FlowRuntimeSnapshot,
    FlowRuntimeStep,
    FlowStepRuntimeState,
)


class FlowRuntimeService:
    def __init__(self, repository: DecisionRepository) -> None:
        self._repository = repository

    def get_runtime(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
    ) -> FlowRuntimeSnapshot:
        session = self._repository.get_session(session_id)
        if session is None or session.actor_id != actor_id:
            raise DomainError(
                "WEIGH_SESSION_NOT_FOUND",
                "Weigh session not found",
                404,
            )

        case = self._repository.get_case_version(session.case_version_id)
        if case is None:
            raise DomainError(
                "CASE_VERSION_STALE",
                "Case version is no longer available",
                409,
            )
        flow = case.resolved_flow
        if flow is None:
            raise DomainError(
                "FLOW_RUNTIME_UNAVAILABLE",
                "CaseVersion does not contain a pinned resolved Flow",
                409,
            )

        steps = self._evaluate(flow=flow, session_state=session.state)
        support = self._execution_support(flow)
        return FlowRuntimeSnapshot(
            session_id=session.id,
            case_version_id=session.case_version_id,
            session_state=session.state.value,
            template_code=flow.template_code,
            template_version_no=flow.template_version_no,
            entry_step_code=flow.entry_step_code,
            execution_support=support,
            steps=steps,
        )

    @staticmethod
    def _execution_support(flow: ResolvedFlow) -> FlowExecutionSupport:
        decision_count = sum(
            1 for step in flow.steps if step.primitive_code == "DECISION"
        )
        fully_supported_primitives = {
            "CONTEXT",
            "DECISION",
            "COLLECTIVE_RESULT",
        }
        if decision_count > 1:
            return FlowExecutionSupport.PARTIAL
        if any(
            step.primitive_code not in fully_supported_primitives
            for step in flow.steps
        ):
            return FlowExecutionSupport.PARTIAL
        return FlowExecutionSupport.FULL

    def _evaluate(
        self,
        *,
        flow: ResolvedFlow,
        session_state: WeighState,
    ) -> tuple[FlowRuntimeStep, ...]:
        step_by_code = {step.code: step for step in flow.steps}
        if flow.entry_step_code not in step_by_code:
            raise DomainError(
                "FLOW_RUNTIME_UNAVAILABLE",
                "Pinned Flow entry Step is invalid",
                409,
            )

        predecessors: dict[str, set[str]] = {
            step.code: set() for step in flow.steps
        }
        for step in flow.steps:
            for next_code in step.next_step_codes:
                if next_code in predecessors:
                    predecessors[next_code].add(step.code)

        decision_codes = [
            step.code
            for step in flow.steps
            if step.primitive_code == "DECISION"
        ]
        first_decision_code = decision_codes[0] if decision_codes else None

        satisfied: set[str] = set()
        evaluated: dict[str, FlowRuntimeStep] = {}
        remaining = {step.code for step in flow.steps}

        while remaining:
            progressed = False
            for step in flow.steps:
                if step.code not in remaining:
                    continue
                predecessor_set = predecessors[step.code]
                if (
                    step.code != flow.entry_step_code
                    and not predecessor_set.issubset(satisfied)
                ):
                    continue

                runtime_step, transition_satisfied = (
                    self._evaluate_reachable_step(
                        step=step,
                        session_state=session_state,
                        first_decision_code=first_decision_code,
                    )
                )
                evaluated[step.code] = runtime_step
                remaining.remove(step.code)
                if transition_satisfied:
                    satisfied.add(step.code)
                progressed = True

            if not progressed:
                break

        for step in flow.steps:
            if step.code not in remaining:
                continue
            reason_code = "FLOW_PREDECESSOR_PENDING"
            if (
                step.primitive_code == "COLLECTIVE_RESULT"
                and session_state is not WeighState.COMMITTED
            ):
                reason_code = "FLOW_COMMIT_REQUIRED"
            evaluated[step.code] = FlowRuntimeStep(
                code=step.code,
                primitive_code=step.primitive_code,
                capability_codes=step.capability_codes,
                next_step_codes=step.next_step_codes,
                state=FlowStepRuntimeState.BLOCKED,
                reason_code=reason_code,
            )

        return tuple(evaluated[step.code] for step in flow.steps)

    @staticmethod
    def _evaluate_reachable_step(
        *,
        step: FlowStep,
        session_state: WeighState,
        first_decision_code: str | None,
    ) -> tuple[FlowRuntimeStep, bool]:
        if step.primitive_code == "CONTEXT":
            return (
                FlowRuntimeStep(
                    code=step.code,
                    primitive_code=step.primitive_code,
                    capability_codes=step.capability_codes,
                    next_step_codes=step.next_step_codes,
                    state=FlowStepRuntimeState.READY,
                ),
                True,
            )

        if step.primitive_code == "DECISION":
            if step.code != first_decision_code:
                return (
                    FlowRuntimeStep(
                        code=step.code,
                        primitive_code=step.primitive_code,
                        capability_codes=step.capability_codes,
                        next_step_codes=step.next_step_codes,
                        state=FlowStepRuntimeState.UNSUPPORTED,
                        reason_code="FLOW_DECISION_REVISION_REQUIRED",
                    ),
                    False,
                )
            if session_state is WeighState.DRAFT:
                return (
                    FlowRuntimeStep(
                        code=step.code,
                        primitive_code=step.primitive_code,
                        capability_codes=step.capability_codes,
                        next_step_codes=step.next_step_codes,
                        state=FlowStepRuntimeState.READY,
                    ),
                    False,
                )
            if session_state is WeighState.COMMITTED:
                return (
                    FlowRuntimeStep(
                        code=step.code,
                        primitive_code=step.primitive_code,
                        capability_codes=step.capability_codes,
                        next_step_codes=step.next_step_codes,
                        state=FlowStepRuntimeState.COMPLETED,
                    ),
                    True,
                )
            return (
                FlowRuntimeStep(
                    code=step.code,
                    primitive_code=step.primitive_code,
                    capability_codes=step.capability_codes,
                    next_step_codes=step.next_step_codes,
                    state=FlowStepRuntimeState.BLOCKED,
                    reason_code="FLOW_SESSION_NOT_EDITABLE",
                ),
                False,
            )

        if step.primitive_code == "COLLECTIVE_RESULT":
            if session_state is WeighState.COMMITTED:
                return (
                    FlowRuntimeStep(
                        code=step.code,
                        primitive_code=step.primitive_code,
                        capability_codes=step.capability_codes,
                        next_step_codes=step.next_step_codes,
                        state=FlowStepRuntimeState.READY,
                    ),
                    False,
                )
            return (
                FlowRuntimeStep(
                    code=step.code,
                    primitive_code=step.primitive_code,
                    capability_codes=step.capability_codes,
                    next_step_codes=step.next_step_codes,
                    state=FlowStepRuntimeState.BLOCKED,
                    reason_code="FLOW_COMMIT_REQUIRED",
                ),
                False,
            )

        if step.primitive_code == "REFLECTION":
            return (
                FlowRuntimeStep(
                    code=step.code,
                    primitive_code=step.primitive_code,
                    capability_codes=step.capability_codes,
                    next_step_codes=step.next_step_codes,
                    state=FlowStepRuntimeState.UNSUPPORTED,
                    reason_code="FLOW_REFLECTION_RUNTIME_PENDING",
                ),
                False,
            )

        return (
            FlowRuntimeStep(
                code=step.code,
                primitive_code=step.primitive_code,
                capability_codes=step.capability_codes,
                next_step_codes=step.next_step_codes,
                state=FlowStepRuntimeState.UNSUPPORTED,
                reason_code="FLOW_PRIMITIVE_UNSUPPORTED",
            ),
            False,
        )
