from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from uuid import UUID

from kefe_api.modules.editorial_projection.models import (
    ReviewedProposal,
    ReviewedProposalBundle,
)
from kefe_api.modules.ingestion_orchestration.models import (
    Proposal,
    ProposalReviewDecision,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
)


class IngestionReviewedProposalSource:
    """Adapts reviewed ingestion Proposals into the Editorial Projection source port."""

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
        candidate_review = self._repository.get_review_decision(candidate.id)
        if candidate_review is None or candidate_review.id != proposal_review_decision_id:
            return None

        dependency_ids = self._dependency_ids(candidate.payload)
        dependencies: list[ReviewedProposal] = []
        for dependency_id in dependency_ids:
            proposal = self._repository.get_proposal(dependency_id)
            if proposal is None:
                continue
            review = self._repository.get_review_decision(dependency_id)
            if review is None:
                continue
            dependencies.append(self._reviewed(proposal, review, ()))

        return ReviewedProposalBundle(
            candidate=self._reviewed(candidate, candidate_review, dependency_ids),
            dependencies=tuple(dependencies),
        )

    @classmethod
    def _dependency_ids(cls, payload: dict[str, Any]) -> tuple[UUID, ...]:
        raw = payload.get("dependency_ids", ())
        if raw is None:
            return ()
        if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes, dict)):
            raise ValueError("candidate dependency_ids must be a list of UUID values")

        items: list[UUID] = []
        seen: set[UUID] = set()
        for value in raw:
            dependency_id = cls._uuid(value)
            if dependency_id in seen:
                continue
            seen.add(dependency_id)
            items.append(dependency_id)
        return tuple(items)

    @staticmethod
    def _uuid(value: Any) -> UUID:
        if isinstance(value, UUID):
            return value
        if isinstance(value, str):
            try:
                return UUID(value)
            except ValueError as exc:
                raise ValueError("candidate dependency_ids must contain UUID values") from exc
        raise ValueError("candidate dependency_ids must contain UUID values")

    @staticmethod
    def _reviewed(
        proposal: Proposal,
        review: ProposalReviewDecision,
        dependency_ids: tuple[UUID, ...],
    ) -> ReviewedProposal:
        return ReviewedProposal(
            id=proposal.id,
            proposal_kind=proposal.proposal_kind,
            payload_schema_ref=proposal.payload_schema_ref,
            payload_schema_version=proposal.payload_schema_version,
            payload=proposal.payload,
            payload_hash=proposal.payload_hash,
            review_decision_id=review.id,
            review_decision=review.decision.value,
            dependency_ids=dependency_ids,
        )
