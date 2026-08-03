from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.ingestion_orchestration.feed_item_extraction import (
    PAYLOAD_SCHEMA_REF,
    PAYLOAD_SCHEMA_VERSION,
    PROPOSAL_KIND,
)
from kefe_api.modules.ingestion_orchestration.feed_item_materializer import (
    TARGET_KIND,
    FeedItemProposalMaterializer,
)
from kefe_api.modules.ingestion_orchestration.models import (
    ProposalMaterialization,
    ProposalReviewDecisionKind,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)


@dataclass(frozen=True, slots=True)
class SecuredFeedItemMaterializationResult:
    materialization: ProposalMaterialization
    replayed: bool


class SecuredFeedItemMaterializationService:
    def __init__(
        self,
        *,
        orchestration: IngestionOrchestrationService,
        repository: IngestionOrchestrationRepository,
        materializer: FeedItemProposalMaterializer,
        security: AdminSecurityService,
    ) -> None:
        self._orchestration = orchestration
        self._repository = repository
        self._materializer = materializer
        self._security = security

    def materialize(
        self,
        principal: AdminPrincipal,
        *,
        proposal_id: UUID,
        proposal_review_decision_id: UUID,
        now: datetime | None = None,
    ) -> SecuredFeedItemMaterializationResult:
        self._security.authorize(
            principal,
            AdminCapability.SOURCE_VERIFY,
            now=now,
        )
        proposal = self._repository.get_proposal(proposal_id)
        if proposal is None:
            raise DomainError(
                "ADMIN_FEED_ITEM_PROPOSAL_NOT_FOUND",
                "Feed item proposal not found",
                404,
            )
        if (
            proposal.proposal_kind != PROPOSAL_KIND
            or proposal.payload_schema_ref != PAYLOAD_SCHEMA_REF
            or proposal.payload_schema_version != PAYLOAD_SCHEMA_VERSION
        ):
            raise DomainError(
                "ADMIN_FEED_ITEM_PROPOSAL_SCHEMA_INVALID",
                "Proposal is not an exact FEED_ITEM proposal",
                422,
            )

        review = self._repository.get_review_decision(proposal_id)
        if review is None:
            raise DomainError(
                "ADMIN_FEED_ITEM_REVIEW_REQUIRED",
                "An accepted feed item review is required",
                409,
            )
        if review.id != proposal_review_decision_id:
            raise DomainError(
                "ADMIN_FEED_ITEM_REVIEW_MISMATCH",
                "Feed item review decision does not match",
                409,
            )
        if review.decision is not ProposalReviewDecisionKind.ACCEPTED:
            raise DomainError(
                "ADMIN_FEED_ITEM_REVIEW_NOT_ACCEPTED",
                "Feed item review decision is not ACCEPTED",
                409,
            )

        existing = self._repository.find_materialization(
            proposal_id,
            target_kind=TARGET_KIND,
        )
        if existing is not None and (
            existing.review_decision_id != review.id
            or existing.proposal_id != proposal.id
        ):
            raise DomainError(
                "ADMIN_FEED_ITEM_MATERIALIZATION_CONFLICT",
                "Feed item materialization conflicts with existing lineage",
                409,
            )
        try:
            materialization = self._orchestration.materialize_accepted_proposal(
                proposal_id=proposal_id,
                materializer=self._materializer,
            )
        except KeyError as exc:
            raise DomainError(
                "ADMIN_FEED_ITEM_PROPOSAL_NOT_FOUND",
                "Feed item proposal not found",
                404,
            ) from exc
        except ValueError as exc:
            raise DomainError(
                "ADMIN_FEED_ITEM_MATERIALIZATION_CONFLICT",
                "Feed item materialization could not be completed",
                409,
            ) from exc

        if (
            materialization.proposal_id != proposal.id
            or materialization.review_decision_id != review.id
            or materialization.target_kind != TARGET_KIND
        ):
            raise DomainError(
                "ADMIN_FEED_ITEM_MATERIALIZATION_CONFLICT",
                "Feed item materialization returned invalid lineage",
                409,
            )
        return SecuredFeedItemMaterializationResult(
            materialization=materialization,
            replayed=existing is not None,
        )


__all__ = [
    "SecuredFeedItemMaterializationResult",
    "SecuredFeedItemMaterializationService",
]
