from __future__ import annotations

from sqlalchemy import text

from kefe_api.infrastructure.postgres_ingestion_orchestration import (
    PostgresIngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.models import Proposal


class PostgresReviewableIngestionRepository(
    PostgresIngestionOrchestrationRepository
):
    """Adds deterministic pending-review queries to the durable Proposal store."""

    def list_pending_proposals(
        self,
        *,
        proposal_kind: str | None = None,
        limit: int = 50,
    ) -> tuple[Proposal, ...]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        clauses = ["review.proposal_id IS NULL"]
        params: dict[str, object] = {"limit": limit}
        if proposal_kind is not None:
            clauses.append("proposal.proposal_kind = :proposal_kind")
            params["proposal_kind"] = proposal_kind
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT proposal.*
                    FROM ingestion.proposal AS proposal
                    LEFT JOIN ingestion.proposal_review_decision AS review
                      ON review.proposal_id = proposal.id
                    WHERE """
                    + " AND ".join(clauses)
                    + " ORDER BY proposal.created_at, proposal.id LIMIT :limit"
                ),
                params,
            ).mappings().all()
        return tuple(self._proposal(row) for row in rows)
