from datetime import UTC, datetime
from uuid import uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.decision.models import (
    CaseVersion,
    FlowStep,
    ResolvedFlow,
    WeighSession,
    WeighState,
)
from kefe_api.modules.flow_runtime.models import (
    FlowExecutionSupport,
    FlowStepRuntimeState,
)
from kefe_api.modules.flow_runtime.service import FlowRuntimeService


def _case(flow: ResolvedFlow | None) -> CaseVersion:
    case_id = uuid4()
    return CaseVersion(
        id=uuid4(),
        case_id=case_id,
        title="Flow runtime fixture",
        summary="A generic Flow runtime test Case.",
        base_format="DILEMMA",
        primary_domain="DAILY_LIFE",
        content_risk="L0",
        version_no=1,
        questions=(),
        resolved_flow=flow,
    )


def _repository(case: CaseVersion, session: WeighSession) -> InMemoryDecisionRepository:
    repository = InMemoryDecisionRepository(cases=[case], reveals=[])
    repository.save_session_with_event(
        session,
        event_name="weigh.started",
        payload={"case_version_id": str(case.id)},
    )
    return repository


def _standard_flow() -> ResolvedFlow:
    return ResolvedFlow(
        template_code="STANDARD_COMMIT_REVEAL",
        template_version_no=1,
        entry_step_code="CONTEXT",
        steps=(
            FlowStep(
                code="CONTEXT",
                primitive_code="CONTEXT",
                capability_codes=("SOURCE_REVEAL",),
                next_step_codes=("DECISION",),
            ),
            FlowStep(
                code="DECISION",
                primitive_code="DECISION",
                capability_codes=("COMMIT_FIRST", "CONFIDENCE_CAPTURE"),
                next_step_codes=("RESULT",),
            ),
            FlowStep(
                code="RESULT",
                primitive_code="COLLECTIVE_RESULT",
            ),
        ),
    )


def _principle_retest_flow() -> ResolvedFlow:
    return ResolvedFlow(
        template_code="PRINCIPLE_CONTEXT_RETEST",
        template_version_no=1,
        entry_step_code="PRINCIPLE",
        steps=(
            FlowStep(
                code="PRINCIPLE",
                primitive_code="DECISION",
                capability_codes=("PRINCIPLE_FIRST",),
                next_step_codes=("CONTEXT",),
            ),
            FlowStep(
                code="CONTEXT",
                primitive_code="CONTEXT",
                capability_codes=("COUNTERARGUMENT",),
                next_step_codes=("FINAL_DECISION",),
            ),
            FlowStep(
                code="FINAL_DECISION",
                primitive_code="DECISION",
                capability_codes=("COMMIT_FIRST",),
                next_step_codes=("REFLECTION",),
            ),
            FlowStep(
                code="REFLECTION",
                primitive_code="REFLECTION",
                capability_codes=("REFLECTION",),
            ),
        ),
    )


def _session(case: CaseVersion, actor_id, state: WeighState) -> WeighSession:
    return WeighSession(
        id=uuid4(),
        actor_id=actor_id,
        case_id=case.case_id,
        case_version_id=case.id,
        state=state,
        committed_at=datetime.now(UTC) if state is WeighState.COMMITTED else None,
    )


def test_standard_flow_is_full_and_server_gates_result_by_commit() -> None:
    actor_id = uuid4()
    case = _case(_standard_flow())
    draft_session = _session(case, actor_id, WeighState.DRAFT)
    repository = _repository(case, draft_session)
    service = FlowRuntimeService(repository)

    before = service.get_runtime(actor_id=actor_id, session_id=draft_session.id)

    assert before.execution_support is FlowExecutionSupport.FULL
    assert [step.state for step in before.steps] == [
        FlowStepRuntimeState.READY,
        FlowStepRuntimeState.READY,
        FlowStepRuntimeState.BLOCKED,
    ]
    assert before.steps[2].reason_code == "FLOW_COMMIT_REQUIRED"

    committed = _session(case, actor_id, WeighState.COMMITTED)
    repository.save_session_with_event(
        committed,
        event_name="weigh.started",
        payload={"case_version_id": str(case.id)},
    )
    after = service.get_runtime(actor_id=actor_id, session_id=committed.id)

    assert [step.state for step in after.steps] == [
        FlowStepRuntimeState.READY,
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.READY,
    ]
    assert all(step.reason_code is None for step in after.steps)


def test_principle_retest_uses_same_runtime_and_exposes_revision_gap() -> None:
    actor_id = uuid4()
    case = _case(_principle_retest_flow())
    draft_session = _session(case, actor_id, WeighState.DRAFT)
    repository = _repository(case, draft_session)
    service = FlowRuntimeService(repository)

    before = service.get_runtime(actor_id=actor_id, session_id=draft_session.id)
    assert before.execution_support is FlowExecutionSupport.PARTIAL
    assert [step.state for step in before.steps] == [
        FlowStepRuntimeState.READY,
        FlowStepRuntimeState.BLOCKED,
        FlowStepRuntimeState.BLOCKED,
        FlowStepRuntimeState.BLOCKED,
    ]

    committed = _session(case, actor_id, WeighState.COMMITTED)
    repository.save_session_with_event(
        committed,
        event_name="weigh.started",
        payload={"case_version_id": str(case.id)},
    )
    after = service.get_runtime(actor_id=actor_id, session_id=committed.id)

    assert [step.state for step in after.steps] == [
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.READY,
        FlowStepRuntimeState.UNSUPPORTED,
        FlowStepRuntimeState.BLOCKED,
    ]
    assert after.steps[2].reason_code == "FLOW_DECISION_REVISION_REQUIRED"
    assert after.steps[3].reason_code == "FLOW_PREDECESSOR_PENDING"


def test_flow_runtime_is_actor_scoped_and_never_infers_legacy_flow() -> None:
    actor_id = uuid4()
    legacy_case = _case(None)
    session = _session(legacy_case, actor_id, WeighState.DRAFT)
    service = FlowRuntimeService(_repository(legacy_case, session))

    with pytest.raises(DomainError) as wrong_actor:
        service.get_runtime(actor_id=uuid4(), session_id=session.id)
    assert wrong_actor.value.code == "WEIGH_SESSION_NOT_FOUND"

    with pytest.raises(DomainError) as legacy:
        service.get_runtime(actor_id=actor_id, session_id=session.id)
    assert legacy.value.code == "FLOW_RUNTIME_UNAVAILABLE"
