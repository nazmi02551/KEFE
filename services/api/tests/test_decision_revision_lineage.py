from uuid import uuid4

from kefe_api.modules.decision.lineage_in_memory import InMemoryLineageDecisionRepository
from kefe_api.modules.decision.lineage_service import DecisionLineageService
from kefe_api.modules.decision.models import (
    CaseVersion,
    FlowStep,
    Question,
    ResolvedFlow,
)
from kefe_api.modules.decision.service import DecisionService
from kefe_api.modules.flow_runtime.models import FlowExecutionSupport, FlowStepRuntimeState
from kefe_api.modules.flow_runtime.service import FlowRuntimeService


def _fixture():
    actor_id = uuid4()
    case_id = uuid4()
    question_id = uuid4()
    case = CaseVersion(
        id=uuid4(),
        case_id=case_id,
        title="Principle retest",
        summary="Retest the same question after Context exposure.",
        base_format="DILEMMA",
        primary_domain="DAILY_LIFE",
        content_risk="L0",
        version_no=1,
        questions=(
            Question(
                id=question_id,
                prompt="Which option?",
                response_type="SINGLE_CHOICE",
                required=True,
                response_schema={"options": ["A", "B"]},
            ),
        ),
        resolved_flow=ResolvedFlow(
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
        ),
    )
    repository = InMemoryLineageDecisionRepository(cases=[case], reveals=[])
    decision = DecisionService(repository)
    runtime = FlowRuntimeService(repository)
    lineage = DecisionLineageService(repository, runtime)
    session = decision.start_session(actor_id=actor_id, case_id=case_id)
    return actor_id, question_id, repository, decision, runtime, lineage, session


def test_principle_context_retest_builds_generic_revision_lineage() -> None:
    actor_id, question_id, repository, decision, runtime, lineage, session = _fixture()

    before = runtime.get_runtime(actor_id=actor_id, session_id=session.id)
    assert before.execution_support is FlowExecutionSupport.PARTIAL
    assert [item.state for item in before.steps] == [
        FlowStepRuntimeState.READY,
        FlowStepRuntimeState.BLOCKED,
        FlowStepRuntimeState.BLOCKED,
        FlowStepRuntimeState.BLOCKED,
    ]

    decision.update_responses(
        actor_id=actor_id,
        session_id=session.id,
        responses={question_id: "A"},
    )
    decision.commit(
        actor_id=actor_id,
        session_id=session.id,
        idempotency_key="initial-commit-0001",
    )

    revisions = repository.list_decision_revisions(session.id)
    assert len(revisions) == 1
    assert revisions[0].revision_no == 1
    assert revisions[0].flow_step_code == "PRINCIPLE"
    assert revisions[0].contribution_class.value == "CORE_PRE_RESULT"

    after_initial = runtime.get_runtime(actor_id=actor_id, session_id=session.id)
    assert [item.state for item in after_initial.steps] == [
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.READY,
        FlowStepRuntimeState.BLOCKED,
        FlowStepRuntimeState.BLOCKED,
    ]

    exposure, intervention = lineage.record_flow_step_exposure(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="CONTEXT",
        idempotency_key="context-exposure-0001",
    )
    assert exposure.resource_category == "CONTEXT"
    assert intervention is not None
    assert intervention.type_code == "CONTEXT_REVEAL"

    repeated_exposure, repeated_intervention = lineage.record_flow_step_exposure(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="CONTEXT",
        idempotency_key="context-exposure-0001",
    )
    assert repeated_exposure.id == exposure.id
    assert repeated_intervention is not None
    assert repeated_intervention.id == intervention.id

    after_context = runtime.get_runtime(actor_id=actor_id, session_id=session.id)
    assert [item.state for item in after_context.steps] == [
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.READY,
        FlowStepRuntimeState.BLOCKED,
    ]

    draft = lineage.update_revision_responses(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="FINAL_DECISION",
        responses={question_id: "B"},
    )
    assert draft.responses == {question_id: "B"}

    committed = lineage.commit_revision(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="FINAL_DECISION",
        idempotency_key="revision-commit-0001",
    )
    assert committed.revision is not None
    assert committed.revision.revision_no == 2
    assert committed.revision.flow_step_code == "FINAL_DECISION"
    assert committed.delta is not None
    assert committed.delta.from_revision_id == revisions[0].id
    assert committed.delta.to_revision_id == committed.revision.id
    assert committed.delta.intervention_ids == (intervention.id,)
    assert committed.delta.diff_snapshot == {
        "changed_question_ids": [str(question_id)],
        "changed_count": 1,
    }

    final_runtime = runtime.get_runtime(actor_id=actor_id, session_id=session.id)
    assert [item.state for item in final_runtime.steps] == [
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.UNSUPPORTED,
    ]
    assert final_runtime.steps[-1].reason_code == "FLOW_REFLECTION_RUNTIME_PENDING"

    snapshot = lineage.lineage(actor_id=actor_id, session_id=session.id)
    assert len(snapshot.revisions) == 2
    assert len(snapshot.exposures) == 1
    assert len(snapshot.interventions) == 1
    assert len(snapshot.deltas) == 1
    assert snapshot.revisions[1].contribution_class.value == "CORE_PRE_RESULT"


def test_lineage_is_actor_scoped() -> None:
    actor_id, _, _, _, _, lineage, session = _fixture()
    assert lineage.lineage(actor_id=actor_id, session_id=session.id).session_id == session.id

    try:
        lineage.lineage(actor_id=uuid4(), session_id=session.id)
    except Exception as exc:
        assert getattr(exc, "code", None) == "WEIGH_SESSION_NOT_FOUND"
    else:
        raise AssertionError("foreign actor must not read Decision lineage")
