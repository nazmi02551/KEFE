from __future__ import annotations

from uuid import UUID

from kefe_api.modules.editorial_projection.models import (
    ReviewedProposal,
    ReviewedProposalBundle,
)
from kefe_api.modules.ingestion_orchestration.models import Proposal
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
)


class IngestionReviewedProposalSource:
    """Adapts terminally reviewed provider-neutral Proposals for projection."""

    def __init__(self, repository: IngestionOrchestrationRepository) -> None:
        self._repository = repository

    def get_bundle(
        self,
        candidate_proposal_id: UUID,
        proposal_review_decision_id: UUID,
    ) -> ReviewedProposalBundle | None:
        candidate = self._repository.get_proposal(candidate_proposal_id)
        if candidate is None:
            return None
        review = self._repository.get_review_decision(candidate_proposal_id)
        if review is None or review.id != proposal_review_decision_id:
            return None

        dependency_ids = tuple(
            UUID(str(value))
            for value in candidate.payload.get("dependency_proposal_ids", [])
        )
        dependencies: list[ReviewedProposal] = []
        for dependency_id in dependency_ids:
            proposal = self._repository.get_proposal(dependency_id)
            dependency_review = self._repository.get_review_decision(dependency_id)
            if proposal is None or dependency_review is None:
                continue
            dependencies.append(self._map(proposal, dependency_review))

        return ReviewedProposalBundle(
            candidate=self._map(candidate, review, dependency_ids=dependency_ids),
            dependencies=tuple(dependencies),
        )

    @staticmethod
    def _map(proposal: Proposal, review, *, dependency_ids=()) -> ReviewedProposal:
        return ReviewedProposal(
            id=proposal.id,
            proposal_kind=proposal.proposal_kind,
            payload_schema_ref=proposal.payload_schema_ref,
            payload_schema_version=proposal.payload_schema_version,
            payload=proposal.payload,
            payload_hash=proposal.payload_hash,
            review_decision_id=review.id,
            review_decision=review.decision.value,
            dependency_ids=tuple(dependency_ids),
        )
