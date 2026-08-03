from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.ingestion_orchestration.models import (
    ProposalReviewDecisionKind,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
)

_FEED_ITEM_KIND = "FEED_ITEM"
_FEED_ITEM_SCHEMA_REF = "kefe.feed-item"
_FEED_ITEM_SCHEMA_VERSION = "1.0.0"
_FEED_ITEM_RISK_CODE = "UNREVIEWED_EXTERNAL_FEED_ITEM"
_TARGET_KIND = "NORMALIZED_ARTIFACT"


class FeedItemMaterializationStatus(StrEnum):
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    READY = "READY"
    MATERIALIZED = "MATERIALIZED"


@dataclass(frozen=True, slots=True)
class FeedItemMaterializationStatusSnapshot:
    proposal_id: UUID
    status: FeedItemMaterializationStatus
    proposal_review_decision_id: UUID | None
    proposal_review_decision: ProposalReviewDecisionKind | None
    proposal_materialization_id: UUID | None
    target_kind: str | None
    target_id: UUID | None
    materialized_at: datetime | None

    def __post_init__(self) -> None:
        if type(self.status) is not FeedItemMaterializationStatus:
            raise ValueError("status must be exact FeedItemMaterializationStatus")
        review_fields = (
            self.proposal_review_decision_id,
            self.proposal_review_decision,
        )
        if (review_fields[0] is None) != (review_fields[1] is None):
            raise ValueError("review identity and decision must be present together")
        materialization_fields = (
            self.proposal_materialization_id,
            self.target_kind,
            self.target_id,
            self.materialized_at,
        )
        if self.status is FeedItemMaterializationStatus.MATERIALIZED:
            if any(value is None for value in materialization_fields):
                raise ValueError("MATERIALIZED status requires target identity")
            if self.target_kind != _TARGET_KIND:
                raise ValueError("MATERIALIZED status requires NORMALIZED_ARTIFACT")
            if self.proposal_review_decision is not ProposalReviewDecisionKind.ACCEPTED:
                raise ValueError("MATERIALIZED status requires ACCEPTED review")
        elif any(value is not None for value in materialization_fields):
            raise ValueError("non-materialized status cannot expose target identity")
        if self.status is FeedItemMaterializationStatus.READY:
            if self.proposal_review_decision is not ProposalReviewDecisionKind.ACCEPTED:
                raise ValueError("READY status requires ACCEPTED review")
        if self.status is FeedItemMaterializationStatus.REVIEW_REQUIRED:
            if self.proposal_review_decision is ProposalReviewDecisionKind.ACCEPTED:
                raise ValueError("REVIEW_REQUIRED cannot contain ACCEPTED review")


class SecuredFeedItemMaterializationStatusService:
    """Read-only persisted lifecycle observation for exact FEED_ITEM proposals."""

    def __init__(
        self,
        *,
        repository: IngestionOrchestrationRepository,
        security: AdminSecurityService,
    ) -> None:
        self._repository = repository
        self._security = security

    def observe(
        self,
        principal: AdminPrincipal,
        *,
        proposal_id: UUID,
        now: datetime | None = None,
    ) -> FeedItemMaterializationStatusSnapshot:
        self._security.authorize(
            principal,
            AdminCapability.CONTENT_REVIEW,
            now=now,
        )
        self._security.authorize(
            principal,
            AdminCapability.SOURCE_VERIFY,
            now=now,
        )

        proposal = self._repository.get_proposal(proposal_id)
        if proposal is None:
            raise DomainError(
                "INGESTION_PROPOSAL_NOT_FOUND",
                "Proposal not found",
                404,
            )
        if (
            proposal.proposal_kind != _FEED_ITEM_KIND
            or proposal.payload_schema_ref != _FEED_ITEM_SCHEMA_REF
            or proposal.payload_schema_version != _FEED_ITEM_SCHEMA_VERSION
            or proposal.risk_code != _FEED_ITEM_RISK_CODE
            or proposal.ai_execution_ref is not None
        ):
            raise DomainError(
                "INGESTION_FEED_ITEM_MATERIALIZATION_UNSUPPORTED",
                "Proposal is not an eligible FEED_ITEM materialization candidate",
                422,
            )

        review = self._repository.get_review_decision(proposal_id)
        materialization = self._repository.find_materialization(proposal_id)
        if materialization is not None:
            if (
                materialization.proposal_id != proposal.id
                or materialization.target_kind != _TARGET_KIND
                or review is None
                or review.proposal_id != proposal.id
                or review.decision is not ProposalReviewDecisionKind.ACCEPTED
                or materialization.review_decision_id != review.id
            ):
                raise DomainError(
                    "INGESTION_FEED_ITEM_MATERIALIZATION_STATUS_CONFLICT",
                    "Persisted feed item materialization state is inconsistent",
                    409,
                )
            return FeedItemMaterializationStatusSnapshot(
                proposal_id=proposal.id,
                status=FeedItemMaterializationStatus.MATERIALIZED,
                proposal_review_decision_id=review.id,
                proposal_review_decision=review.decision,
                proposal_materialization_id=materialization.id,
                target_kind=materialization.target_kind,
                target_id=materialization.target_id,
                materialized_at=materialization.materialized_at,
            )

        if review is not None and review.proposal_id != proposal.id:
            raise DomainError(
                "INGESTION_FEED_ITEM_MATERIALIZATION_STATUS_CONFLICT",
                "Persisted feed item review state is inconsistent",
                409,
            )
        if review is not None and review.decision is ProposalReviewDecisionKind.ACCEPTED:
            return FeedItemMaterializationStatusSnapshot(
                proposal_id=proposal.id,
                status=FeedItemMaterializationStatus.READY,
                proposal_review_decision_id=review.id,
                proposal_review_decision=review.decision,
                proposal_materialization_id=None,
                target_kind=None,
                target_id=None,
                materialized_at=None,
            )
        return FeedItemMaterializationStatusSnapshot(
            proposal_id=proposal.id,
            status=FeedItemMaterializationStatus.REVIEW_REQUIRED,
            proposal_review_decision_id=review.id if review is not None else None,
            proposal_review_decision=review.decision if review is not None else None,
            proposal_materialization_id=None,
            target_kind=None,
            target_id=None,
            materialized_at=None,
        )


__all__ = [
    "FeedItemMaterializationStatus",
    "FeedItemMaterializationStatusSnapshot",
    "SecuredFeedItemMaterializationStatusService",
]
