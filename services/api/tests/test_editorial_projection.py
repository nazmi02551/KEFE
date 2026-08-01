from __future__ import annotations

from dataclasses import replace
from uuid import UUID, uuid4

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.content_authoring.models import ContentLifecycle
from kefe_api.modules.editorial_projection.in_memory import (
    InMemoryEditorialProjectionProfileRegistry,
    InMemoryEditorialProjectionRepository,
    InMemoryReviewedProposalSource,
)
from kefe_api.modules.editorial_projection.models import (
    EditorialProjectionCommand,
    EditorialProjectionProfile,
    ReviewedProposal,
    ReviewedProposalBundle,
    stable_payload_hash,
)
from kefe_api.modules.editorial_projection.service import EditorialProjectionService


def _proposal(
    kind: str,
    payload: dict,
    *,
    proposal_id: UUID | None = None,
    review_decision: str = "ACCEPTED",
    dependency_ids: tuple[UUID, ...] = (),
) -> ReviewedProposal:
    return ReviewedProposal(
        id=proposal_id or uuid4(),
        proposal_kind=kind,
        payload_schema_ref=(
            "kefe.candidate-case" if kind == "CANDIDATE_CASE" else f"kefe.{kind.lower()}"
        ),
        payload_schema_version="1.0.0",
        payload=payload,
        payload_hash=stable_payload_hash(payload),
        review_decision_id=uuid4(),
        review_decision=review_decision,
        dependency_ids=dependency_ids,
    )


def _bundle(*, accepted: bool = True, include_flow: bool = True):
    decision_problem = _proposal("DECISION_PROBLEM", {"title": "Seat allocation"})
    question_draft = _proposal(
        "QUESTION_DRAFT",
        {"prompt": "Should children sit with a parent?"},
    )
    source_id = uuid4()
    payload = {
        "slug": f"candidate-{uuid4().hex[:8]}",
        "title": "Should children be seated with a parent?",
        "summary": "A reviewed Candidate Case projected into authoring.",
        "base_format_code": "DILEMMA",
        "primary_domain_code": "TRAVEL",
        "content_risk": "L1",
        "content_locale": "en",
        "is_fact_bearing": True,
        "required_review_modes": ["EDITORIAL"],
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
        "sources": [
            {
                "id": str(source_id),
                "source_kind": "OFFICIAL",
                "locator": "https://example.test/policy",
                "title": "Seat policy",
                "claim_status": "CLAIMED",
                "verified": False,
            }
        ],
        "context_blocks": [
            {
                "title": "Current policy",
                "body": "The policy is under editorial review.",
                "disclosure_level": "ESSENTIAL",
                "claim_status": "CLAIMED",
                "source_ids": [str(source_id)],
            }
        ],
    }
    if include_flow:
        payload.update(
            {
                "flow_template_code": "STANDARD_COMMIT_REVEAL",
                "flow_template_version_no": 1,
            }
        )
    candidate = _proposal(
        "CANDIDATE_CASE",
        payload,
        review_decision="ACCEPTED" if accepted else "CHANGES_REQUESTED",
        dependency_ids=(decision_problem.id, question_draft.id),
    )
    return ReviewedProposalBundle(
        candidate=candidate,
        dependencies=(decision_problem, question_draft),
    )


def _service(bundle: ReviewedProposalBundle):
    repository = InMemoryEditorialProjectionRepository()
    profile = EditorialProjectionProfile(
        profile_code="CANDIDATE_TO_AUTHORING",
        profile_version=1,
        candidate_schema_ref="kefe.candidate-case",
        candidate_schema_version="1.0.0",
        required_dependency_kinds=frozenset(
            {"DECISION_PROBLEM", "QUESTION_DRAFT"}
        ),
    )
    service = EditorialProjectionService(
        InMemoryReviewedProposalSource((bundle,)),
        InMemoryEditorialProjectionProfileRegistry((profile,)),
        repository,
    )
    command = EditorialProjectionCommand(
        candidate_proposal_id=bundle.candidate.id,
        proposal_review_decision_id=bundle.candidate.review_decision_id,
        profile_code=profile.profile_code,
        profile_version=profile.profile_version,
        idempotency_key="projection-attempt-1",
        requested_by_admin_ref="admin:test",
    )
    return service, repository, command


def test_projection_creates_existing_authoring_draft_only() -> None:
    bundle = _bundle()
    service, repository, command = _service(bundle)

    result = service.project(command)

    assert result.replayed is False
    draft = repository.authoring_repository.get_version(
        result.record.authoring_case_version_id
    )
    assert draft is not None
    assert draft.state is ContentLifecycle.DRAFT
    assert draft.flow_template_code == "STANDARD_COMMIT_REVEAL"
    assert draft.flow_template_version_no == 1
    assert draft.issues[0].questions[0].response_schema == {
        "options": ["YES", "NO"]
    }
    assert draft.completed_review_modes == ()
    assert repository.authoring_repository.list_audit(draft.case_id)[0].command == (
        "project_candidate_case"
    )


def test_projection_replay_is_idempotent_and_candidate_cannot_fork() -> None:
    bundle = _bundle()
    service, repository, command = _service(bundle)

    first = service.project(command)
    replay = service.project(command)

    assert replay.replayed is True
    assert replay.record == first.record
    assert len(
        repository.authoring_repository.list_versions(first.record.authoring_case_id)
    ) == 1

    with pytest.raises(DomainError) as raised:
        service.project(replace(command, idempotency_key="projection-attempt-2"))
    assert raised.value.code == "EDITORIAL_PROJECTION_CANDIDATE_ALREADY_PROJECTED"


def test_projection_requires_accepted_candidate_dependencies_and_explicit_flow() -> None:
    rejected = _bundle(accepted=False)
    service, _, command = _service(rejected)
    with pytest.raises(DomainError) as raised:
        service.project(command)
    assert raised.value.code == "EDITORIAL_PROJECTION_SOURCE_NOT_ACCEPTED"

    incomplete = _bundle()
    incomplete = replace(incomplete, dependencies=incomplete.dependencies[:1])
    service, _, command = _service(incomplete)
    with pytest.raises(DomainError) as raised:
        service.project(command)
    assert raised.value.code == "EDITORIAL_PROJECTION_DEPENDENCY_NOT_READY"

    no_flow = _bundle(include_flow=False)
    service, _, command = _service(no_flow)
    with pytest.raises(DomainError) as raised:
        service.project(command)
    assert raised.value.code == "EDITORIAL_PROJECTION_FLOW_REFERENCE_INVALID"


def test_command_flow_selection_is_explicit_and_profile_governed() -> None:
    bundle = _bundle(include_flow=False)
    service, repository, command = _service(bundle)
    command = replace(
        command,
        explicit_flow_template_code="STANDARD_COMMIT_REVEAL",
        explicit_flow_template_version=1,
    )

    result = service.project(command)

    draft = repository.authoring_repository.get_version(
        result.record.authoring_case_version_id
    )
    assert draft is not None
    assert draft.flow_template_code == "STANDARD_COMMIT_REVEAL"
