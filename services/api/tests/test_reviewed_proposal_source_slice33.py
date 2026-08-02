from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.editorial_projection import (
    SecuredEditorialProjectionService,
)
from kefe_api.modules.admin_security.models import AdminPrincipal, AdminRole
from kefe_api.modules.admin_security.policy import default_admin_security_policy
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.editorial_projection.in_memory import (
    InMemoryEditorialProjectionProfileRegistry,
    InMemoryEditorialProjectionRepository,
)
from kefe_api.modules.editorial_projection.ingestion_source import (
    IngestionReviewedProposalSource,
)
from kefe_api.modules.editorial_projection.models import EditorialProjectionProfile
from kefe_api.modules.editorial_projection.service import EditorialProjectionService
from kefe_api.modules.ingestion_orchestration.in_memory import (
    InMemoryIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.models import (
    ExecutorKind,
    IngestionRunState,
    InputArtifactKind,
    ProposalDraft,
    ProposalReviewDecisionKind,
    StageProcessorResult,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)


@dataclass
class StaticProcessor:
    drafts: tuple[ProposalDraft, ...]

    def process(self, **_kwargs) -> StageProcessorResult:
        return StageProcessorResult(proposals=self.drafts)


class UnusedSessionResolver:
    def resolve(self, _token):
        raise AssertionError("session resolution is not used by direct facade tests")

    def mark_seen(self, _session_id, *, seen_at):
        raise AssertionError(f"mark_seen must not be called: {seen_at}")


def _principal(role: AdminRole) -> AdminPrincipal:
    now = datetime.now(UTC)
    return AdminPrincipal(
        admin_subject_id=uuid4(),
        session_id=uuid4(),
        roles=frozenset({role}),
        direct_capabilities=frozenset(),
        authenticated_at=now - timedelta(minutes=1),
        mfa_satisfied_at=now - timedelta(minutes=1),
        step_up_at=None,
        expires_at=now + timedelta(hours=1),
        last_seen_at=now - timedelta(seconds=5),
    )


def _build_reviewed_store():
    repository = InMemoryIngestionOrchestrationRepository()
    service = IngestionOrchestrationService(repository)
    run = service.start_run(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash="source-hash",
        pipeline_code="candidate-extraction",
        pipeline_version="1.0.0",
        configuration_hash="config-hash",
        locale="en",
    )

    dependencies = (
        ProposalDraft(
            proposal_kind="DECISION_PROBLEM",
            payload_schema_ref="kefe.decision_problem",
            payload_schema_version="1.0.0",
            payload={"title": "Seat allocation"},
        ),
        ProposalDraft(
            proposal_kind="QUESTION_DRAFT",
            payload_schema_ref="kefe.question_draft",
            payload_schema_version="1.0.0",
            payload={"prompt": "Should children sit with a parent?"},
        ),
    )
    service.execute_stage(
        run_id=run.id,
        stage_code="extract-dependencies",
        stage_version="1.0.0",
        input_hash="input-1",
        max_attempts=2,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=StaticProcessor(dependencies),
    )
    dependency_proposals = repository.list_proposals(run.id)
    dependency_ids = [str(item.id) for item in dependency_proposals]

    candidate_payload = {
        "slug": f"reviewed-{uuid4().hex[:8]}",
        "title": "Should children sit with a parent?",
        "summary": "Reviewed Candidate Case from the active Proposal store.",
        "base_format_code": "DILEMMA",
        "primary_domain_code": "TRAVEL",
        "content_risk": "L1",
        "dependency_proposal_ids": dependency_ids,
        "issues": [
            {
                "code": "PRIMARY",
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
        "flow_template_code": "STANDARD_COMMIT_REVEAL",
        "flow_template_version_no": 1,
    }
    service.execute_stage(
        run_id=run.id,
        stage_code="compose-candidate",
        stage_version="1.0.0",
        input_hash="input-2",
        max_attempts=1,
        executor_kind=ExecutorKind.DETERMINISTIC,
        processor=StaticProcessor(
            (
                ProposalDraft(
                    proposal_kind="CANDIDATE_CASE",
                    payload_schema_ref="kefe.candidate-case",
                    payload_schema_version="1.0.0",
                    payload=candidate_payload,
                ),
            )
        ),
    )
    all_proposals = repository.list_proposals(run.id)
    candidate = next(item for item in all_proposals if item.proposal_kind == "CANDIDATE_CASE")
    reviews = {}
    for proposal in all_proposals:
        reviews[proposal.id] = service.review_proposal(
            proposal_id=proposal.id,
            decision=ProposalReviewDecisionKind.ACCEPTED,
            reviewer_ref=f"reviewer:{proposal.id}",
        )
    service.mark_succeeded(run.id)
    assert repository.get_run(run.id).state is IngestionRunState.SUCCEEDED
    return repository, candidate, reviews


def test_active_store_is_replay_safe_and_review_is_terminal() -> None:
    repository = InMemoryIngestionOrchestrationRepository()
    service = IngestionOrchestrationService(repository)
    args = dict(
        input_artifact_kind=InputArtifactKind.SOURCE_ARTIFACT,
        input_artifact_id=uuid4(),
        input_content_hash="same-source",
        pipeline_code="candidate-extraction",
        pipeline_version="1",
        configuration_hash="same-config",
    )
    first = service.start_run(**args)
    replay = service.start_run(**args)
    assert replay.id == first.id
    assert replay.run_key == first.run_key


def test_reviewed_source_and_secured_facade_project_existing_draft() -> None:
    ingestion_repository, candidate, reviews = _build_reviewed_store()
    projection_repository = InMemoryEditorialProjectionRepository()
    projection = EditorialProjectionService(
        IngestionReviewedProposalSource(ingestion_repository),
        InMemoryEditorialProjectionProfileRegistry(
            (
                EditorialProjectionProfile(
                    profile_code="CANDIDATE_TO_AUTHORING",
                    profile_version=1,
                    candidate_schema_ref="kefe.candidate-case",
                    candidate_schema_version="1.0.0",
                    required_dependency_kinds=frozenset(
                        {"DECISION_PROBLEM", "QUESTION_DRAFT"}
                    ),
                ),
            )
        ),
        projection_repository,
    )
    secured = SecuredEditorialProjectionService(
        projection=projection,
        security=AdminSecurityService(
            session_resolver=UnusedSessionResolver(),
            policy=default_admin_security_policy(),
        ),
    )
    editor = _principal(AdminRole.EDITOR)

    result = secured.project(
        editor,
        candidate_proposal_id=candidate.id,
        proposal_review_decision_id=reviews[candidate.id].id,
        profile_code="CANDIDATE_TO_AUTHORING",
        profile_version=1,
        idempotency_key="secured-projection-1",
    )

    assert result.replayed is False
    assert result.record.requested_by_admin_ref == editor.audit_actor_ref
    draft = projection_repository.authoring_repository.get_version(
        result.record.authoring_case_version_id
    )
    assert draft is not None
    assert draft.title == candidate.payload["title"]


def test_projection_requires_dedicated_editor_capability() -> None:
    ingestion_repository, candidate, reviews = _build_reviewed_store()
    projection = EditorialProjectionService(
        IngestionReviewedProposalSource(ingestion_repository),
        InMemoryEditorialProjectionProfileRegistry(
            (
                EditorialProjectionProfile(
                    profile_code="CANDIDATE_TO_AUTHORING",
                    profile_version=1,
                    candidate_schema_ref="kefe.candidate-case",
                    candidate_schema_version="1.0.0",
                    required_dependency_kinds=frozenset(
                        {"DECISION_PROBLEM", "QUESTION_DRAFT"}
                    ),
                ),
            )
        ),
        InMemoryEditorialProjectionRepository(),
    )
    secured = SecuredEditorialProjectionService(
        projection=projection,
        security=AdminSecurityService(
            session_resolver=UnusedSessionResolver(),
            policy=default_admin_security_policy(),
        ),
    )

    with pytest.raises(DomainError) as raised:
        secured.project(
            _principal(AdminRole.REVIEWER),
            candidate_proposal_id=candidate.id,
            proposal_review_decision_id=reviews[candidate.id].id,
            profile_code="CANDIDATE_TO_AUTHORING",
            profile_version=1,
            idempotency_key="forbidden-projection",
        )
    assert raised.value.code == "ADMIN_FORBIDDEN"
    assert raised.value.meta["required_capability"] == "CONTENT_PROJECT"
