from uuid import uuid4

from kefe_api.modules.decision.lineage_service import DecisionLineageService
from kefe_api.modules.decision.models import (
    CaseVersion,
    FlowStep,
    Question,
    ResolvedFlow,
)
from kefe_api.modules.decision.reflection_in_memory import (
    InMemoryReflectionDecisionRepository,
)
from kefe_api.modules.decision.reflection_service import ReflectionService
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
    repository = InMemoryReflectionDecisionRepository(cases=[case], reveals=[])
    decision = DecisionService(repository)
    runtime = FlowRuntimeService(repository)
    lineage = DecisionLineageService(repository, runtime)
    reflection = ReflectionService(repository, runtime)
    session = decision.start_session(actor_id=actor_id, case_id=case_id)
    return actor_id, question_id, repository, decision, runtime, lineage, reflection, session


def test_principle_context_retest_builds_generic_revision_and_reflection_lineage() -> None:
    (
        actor_id,
        question_id,
        repository,
        decision,
        runtime,
        lineage,
        reflection,
        session,
    ) = _fixture()

    before = runtime.get_runtime(actor_id=actor_id, session_id=session.id)
    assert before.execution_support is FlowExecutionSupport.FULL
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
    assert revisions[0].flow_step_code == "PRINCIPLE"

    exposure, intervention = lineage.record_flow_step_exposure(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="CONTEXT",
        idempotency_key="context-exposure-0001",
    )
    assert exposure.resource_category == "CONTEXT"
    assert intervention is not None
    assert intervention.type_code == "CONTEXT_REVEAL"

    lineage.update_revision_responses(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="FINAL_DECISION",
        responses={question_id: "B"},
    )
    committed = lineage.commit_revision(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="FINAL_DECISION",
        idempotency_key="revision-commit-0001",
    )
    assert committed.revision is not None
    assert committed.delta is not None
    assert committed.delta.intervention_ids == (intervention.id,)
    assert committed.delta.diff_snapshot["changed_count"] == 1

    reflection_ready = runtime.get_runtime(actor_id=actor_id, session_id=session.id)
    assert [item.state for item in reflection_ready.steps] == [
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.COMPLETED,
        FlowStepRuntimeState.READY,
    ]

    model = reflection.read(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="REFLECTION",
    )
    assert model.revision_count == 2
    assert model.latest_revision_id == committed.revision.id
    assert model.latest_delta_id == committed.delta.id
    assert model.decision_changed is True
    assert model.changed_question_count == 1
    assert model.intervention_count == 1
    assert model.intervention_type_codes == ("CONTEXT_REVEAL",)
    assert model.completed is False

    revision_count = len(repository.list_decision_revisions(session.id))
    intervention_count = len(repository.list_interventions(session.id))
    completion = reflection.complete(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="REFLECTION",
        idempotency_key="reflection-complete-0001",
    )
    replay = reflection.complete(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="REFLECTION",
        idempotency_key="reflection-complete-0001",
    )
    assert replay.id == completion.id
    assert len(repository.list_decision_revisions(session.id)) == revision_count
    assert len(repository.list_interventions(session.id)) == intervention_count

    completed_runtime = runtime.get_runtime(actor_id=actor_id, session_id=session.id)
    assert completed_runtime.steps[-1].state is FlowStepRuntimeState.COMPLETED
    assert reflection.read(
        actor_id=actor_id,
        session_id=session.id,
        flow_step_code="REFLECTION",
    ).completed is True


def test_lineage_is_actor_scoped() -> None:
    actor_id, _, _, _, _, lineage, _, session = _fixture()
    assert lineage.lineage(actor_id=actor_id, session_id=session.id).session_id == session.id

    try:
        lineage.lineage(actor_id=uuid4(), session_id=session.id)
    except Exception as exc:
        assert getattr(exc, "code", None) == "WEIGH_SESSION_NOT_FOUND"
    else:
        raise AssertionError("foreign actor must not read Decision lineage")
