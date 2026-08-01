from __future__ import annotations

from uuid import uuid4

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


class ConcurrentWinnerRepository:
    """Simulate another transaction committing before this caller sees conflict."""

    def __init__(self) -> None:
        self.delegate = InMemoryEditorialProjectionRepository()

    def get_by_idempotency(self, candidate_proposal_id, idempotency_key):
        return self.delegate.get_by_idempotency(
            candidate_proposal_id,
            idempotency_key,
        )

    def get_by_candidate(self, candidate_proposal_id):
        return self.delegate.get_by_candidate(candidate_proposal_id)

    def create_atomically(self, *, identity, initial_version, audit, record) -> None:
        self.delegate.create_atomically(
            identity=identity,
            initial_version=initial_version,
            audit=audit,
            record=record,
        )
        raise ValueError("simulated concurrent unique conflict")


def test_concurrent_same_idempotency_recovers_as_replay() -> None:
    payload = {
        "slug": f"concurrent-{uuid4().hex[:8]}",
        "title": "Concurrent candidate",
        "summary": "Concurrent retry recovery.",
        "base_format_code": "DILEMMA",
        "primary_domain_code": "DAILY_LIFE",
        "content_risk": "L0",
        "issues": [
            {
                "code": "PRIMARY",
                "title": "Primary",
                "questions": [
                    {
                        "stable_code": "PRIMARY_DECISION",
                        "prompt": "Choose?",
                        "response_type": "SINGLE_CHOICE",
                        "response_schema": {"options": ["A", "B"]},
                    }
                ],
            }
        ],
        "flow_template_code": "STANDARD_COMMIT_REVEAL",
        "flow_template_version_no": 1,
    }
    candidate = ReviewedProposal(
        id=uuid4(),
        proposal_kind="CANDIDATE_CASE",
        payload_schema_ref="kefe.candidate-case",
        payload_schema_version="1.0.0",
        payload=payload,
        payload_hash=stable_payload_hash(payload),
        review_decision_id=uuid4(),
        review_decision="ACCEPTED",
    )
    bundle = ReviewedProposalBundle(candidate=candidate)
    profile = EditorialProjectionProfile(
        profile_code="CANDIDATE_TO_AUTHORING",
        profile_version=1,
        candidate_schema_ref="kefe.candidate-case",
        candidate_schema_version="1.0.0",
    )
    repository = ConcurrentWinnerRepository()
    service = EditorialProjectionService(
        InMemoryReviewedProposalSource((bundle,)),
        InMemoryEditorialProjectionProfileRegistry((profile,)),
        repository,
    )
    command = EditorialProjectionCommand(
        candidate_proposal_id=candidate.id,
        proposal_review_decision_id=candidate.review_decision_id,
        profile_code=profile.profile_code,
        profile_version=profile.profile_version,
        idempotency_key="same-concurrent-key",
        requested_by_admin_ref="admin:concurrency-test",
    )

    result = service.project(command)

    assert result.replayed is True
    stored = repository.delegate.get_by_idempotency(
        candidate.id,
        command.idempotency_key,
    )
    assert stored == result.record
    assert len(
        repository.delegate.authoring_repository.list_versions(
            result.record.authoring_case_id
        )
    ) == 1
