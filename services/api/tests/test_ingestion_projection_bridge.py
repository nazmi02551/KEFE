from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.content_authoring.models import ContentLifecycle
from kefe_api.modules.editorial_projection.in_memory import (
    InMemoryEditorialProjectionProfileRegistry,
    InMemoryEditorialProjectionRepository,
)
from kefe_api.modules.editorial_projection.ingestion_source import (
    IngestionReviewedProposalSource,
)
from kefe_api.modules.editorial_projection.models import (
    EditorialProjectionCommand,
    EditorialProjectionProfile,
)
from kefe_api.modules.editorial_projection.service import EditorialProjectionService
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    InputArtifactKind,
    Proposal,
    ProposalDraft,
    ProposalReviewDecisionKind,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)


class FixedProcessor:
    def __init__(self, proposal: ProposalDraft) -> None:
        self._proposal = proposal

    def process(self, **_) -> StageProcessorResult:
        return StageProcessorResult(proposals=(self._proposal,))


def _run(service: IngestionOrchestrationService):
    return service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash="sha256:bridge-source",
        pipeline_code="CANDIDATE_COMPOSITION",
        pipeline_version="1",
        configuration_hash="sha256:bridge-config",
        locale="en",
    )


def _add_proposal(
    service: IngestionOrchestrationService,
    repository: InMemoryIngestionOrchestrationRepository,
    *,
    run_id: UUID,
    draft: ProposalDraft,
    stage_code: str,
) -> Proposal:
    before = {item.id for item in repository.list_proposals(run_id)}
    service.execute_stage(
        run_id=run_id,
        stage_code=stage_code,
        stage_version="1",
        input_hash=f"sha256:{stage_code.lower()}",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=FixedProcessor(draft),
    )
    return next(
        item for item in repository.list_proposals(run_id) if item.id not in before
    )


def _candidate_payload(dependency_ids: tuple[UUID, ...]) -> dict:
    return {
        "slug": f"ingestion-bridge-{uuid4().hex[:8]}",
        "title": "Should children sit with a parent?",
        "summary": "An accepted Candidate Case from the ingestion proposal store.",
        "base_format_code": "DILEMMA",
        "primary_domain_code": "TRAVEL",
        "content_risk": "L1",
        "content_locale": "en",
        "flow_template_code": "STANDARD_COMMIT_REVEAL",
        "flow_template_version_no": 1,
        "dependency_ids": [str(item) for item in dependency_ids],
        "issues": [
            {
                "code": "PRIMARY_ISSUE",
                "title": "Seat allocation",
                "questions": [
                    {
                        "stable_code": "PRIMARY_DECISION",
                        "prompt": "Should children sit with a parent?",
                        "response_type": "SINGLE_CHOICE",
                        "response_schema": {"options": ["YES", "NO"]},
                    }
                ],
            }
        ],
    }


def _profile() -> EditorialProjectionProfile:
    return EditorialProjectionProfile(
        profile_code="INGESTION_CANDIDATE_TO_AUTHORING",
        profile_version=1,
        candidate_schema_ref="kefe.candidate-case",
        candidate_schema_version="1.0.0",
        required_dependency_kinds=frozenset({"QUESTION_DRAFT"}),
    )


def _accepted_bundle_fixture():
    repository = InMemoryIngestionOrchestrationRepository()
    ingestion = IngestionOrchestrationService(repository)
    run = _run(ingestion)
    question = _add_proposal(
        ingestion,
        repository,
        run_id=run.id,
        stage_code="QUESTION_PROPOSAL",
        draft=ProposalDraft(
            proposal_kind="QUESTION_DRAFT",
            payload_schema_ref="kefe.question-draft",
            payload_schema_version="1.0.0",
            payload={"prompt": "Should children sit with a parent?"},
        ),
    )
    question_review = ingestion.review_proposal(
        proposal_id=question.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:question-reviewer",
    )
    candidate = _add_proposal(
        ingestion,
        repository,
        run_id=run.id,
        stage_code="CANDIDATE_CASE_COMPOSITION",
        draft=ProposalDraft(
            proposal_kind="CANDIDATE_CASE",
            payload_schema_ref="kefe.candidate-case",
            payload_schema_version="1.0.0",
            payload=_candidate_payload((question.id,)),
        ),
    )
    candidate_review = ingestion.review_proposal(
        proposal_id=candidate.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:candidate-reviewer",
    )
    return repository, candidate, candidate_review, question, question_review


def test_ingestion_source_bridges_accepted_candidate_into_existing_draft() -> None:
    repository, candidate, candidate_review, question, question_review = (
        _accepted_bundle_fixture()
    )
    source = IngestionReviewedProposalSource(repository)
    bundle = source.get_bundle(candidate.id, candidate_review.id)

    assert bundle is not None
    assert bundle.candidate.review_decision == "ACCEPTED"
    assert bundle.candidate.dependency_ids == (question.id,)
    assert bundle.dependencies[0].review_decision_id == question_review.id

    projection_repository = InMemoryEditorialProjectionRepository()
    profile = _profile()
    service = EditorialProjectionService(
        source,
        InMemoryEditorialProjectionProfileRegistry((profile,)),
        projection_repository,
    )
    command = EditorialProjectionCommand(
        candidate_proposal_id=candidate.id,
        proposal_review_decision_id=candidate_review.id,
        profile_code=profile.profile_code,
        profile_version=profile.profile_version,
        idempotency_key="ingestion-bridge-attempt-1",
        requested_by_admin_ref="admin:projector",
    )

    first = service.project(command)
    replay = service.project(command)

    assert first.replayed is False
    assert replay.replayed is True
    draft = projection_repository.authoring_repository.get_version(
        first.record.authoring_case_version_id
    )
    assert draft is not None
    assert draft.state is ContentLifecycle.DRAFT
    assert draft.issues[0].questions[0].stable_code == "PRIMARY_DECISION"


def test_bridge_rejects_mismatched_review_identity() -> None:
    repository, candidate, _, _, _ = _accepted_bundle_fixture()
    source = IngestionReviewedProposalSource(repository)

    assert source.get_bundle(candidate.id, uuid4()) is None


def test_unreviewed_dependency_remains_missing_and_projection_fails_closed() -> None:
    repository = InMemoryIngestionOrchestrationRepository()
    ingestion = IngestionOrchestrationService(repository)
    run = _run(ingestion)
    question = _add_proposal(
        ingestion,
        repository,
        run_id=run.id,
        stage_code="QUESTION_PROPOSAL",
        draft=ProposalDraft(
            proposal_kind="QUESTION_DRAFT",
            payload_schema_ref="kefe.question-draft",
            payload_schema_version="1.0.0",
            payload={"prompt": "Unreviewed dependency"},
        ),
    )
    candidate = _add_proposal(
        ingestion,
        repository,
        run_id=run.id,
        stage_code="CANDIDATE_CASE_COMPOSITION",
        draft=ProposalDraft(
            proposal_kind="CANDIDATE_CASE",
            payload_schema_ref="kefe.candidate-case",
            payload_schema_version="1.0.0",
            payload=_candidate_payload((question.id,)),
        ),
    )
    candidate_review = ingestion.review_proposal(
        proposal_id=candidate.id,
        decision=ProposalReviewDecisionKind.ACCEPTED,
        reviewer_ref="admin:candidate-reviewer",
    )
    source = IngestionReviewedProposalSource(repository)
    profile = _profile()
    service = EditorialProjectionService(
        source,
        InMemoryEditorialProjectionProfileRegistry((profile,)),
        InMemoryEditorialProjectionRepository(),
    )

    with pytest.raises(DomainError) as raised:
        service.project(
            EditorialProjectionCommand(
                candidate_proposal_id=candidate.id,
                proposal_review_decision_id=candidate_review.id,
                profile_code=profile.profile_code,
                profile_version=profile.profile_version,
                idempotency_key="missing-dependency",
                requested_by_admin_ref="admin:projector",
            )
        )

    assert raised.value.code == "EDITORIAL_PROJECTION_DEPENDENCY_NOT_READY"
