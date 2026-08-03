from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.ingestion_orchestration.knowledge_materializer import (
    KnowledgeProposalMaterializer,
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
from kefe_api.modules.knowledge.ports import KnowledgeRepository

_FEED_ITEM_KIND = "FEED_ITEM"
_FEED_ITEM_SCHEMA_REF = "kefe.feed-item"
_FEED_ITEM_SCHEMA_VERSION = "1.0.0"
_FEED_ITEM_RISK_CODE = "UNREVIEWED_EXTERNAL_FEED_ITEM"
_TARGET_KIND = "NORMALIZED_ARTIFACT"


class SecuredFeedItemMaterializationService:
    """Explicit Admin command facade for reviewed FEED_ITEM normalization."""

    def __init__(
        self,
        *,
        orchestration: IngestionOrchestrationService,
        repository: IngestionOrchestrationRepository,
        knowledge: KnowledgeRepository,
        security: AdminSecurityService,
    ) -> None:
        self._orchestration = orchestration
        self._repository = repository
        self._knowledge = knowledge
        self._security = security

    def materialize(
        self,
        principal: AdminPrincipal,
        *,
        proposal_id: UUID,
        proposal_review_decision_id: UUID,
        now: datetime | None = None,
    ) -> ProposalMaterialization:
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
        if review is None or review.decision is not ProposalReviewDecisionKind.ACCEPTED:
            raise DomainError(
                "INGESTION_PROPOSAL_REVIEW_NOT_ACCEPTED",
                "Proposal must have an ACCEPTED review decision",
                409,
            )
        if (
            review.id != proposal_review_decision_id
            or review.proposal_id != proposal.id
        ):
            raise DomainError(
                "INGESTION_PROPOSAL_REVIEW_BINDING_MISMATCH",
                "Proposal review decision binding does not match",
                409,
            )

        existing = self._repository.find_materialization(
            proposal_id,
            target_kind=_TARGET_KIND,
        )
        if existing is not None:
            if existing.review_decision_id != review.id:
                raise DomainError(
                    "INGESTION_PROPOSAL_REVIEW_BINDING_MISMATCH",
                    "Existing materialization uses a different review decision",
                    409,
                )
            return existing

        materializer = KnowledgeProposalMaterializer(
            knowledge_repository=self._knowledge,
            orchestration_repository=self._repository,
        )
        try:
            materialization = self._orchestration.materialize_accepted_proposal(
                proposal_id=proposal_id,
                materializer=materializer,
            )
        except KeyError as exc:
            raise DomainError(
                "INGESTION_PROPOSAL_NOT_FOUND",
                "Proposal not found",
                404,
            ) from exc
        except ValueError as exc:
            message = str(exc)
            if (
                "conflicting normalized artifact" in message
                or "persistence invariant" in message
            ):
                raise DomainError(
                    "INGESTION_FEED_ITEM_MATERIALIZATION_CONFLICT",
                    "Feed item materialization conflicts with persisted state",
                    409,
                ) from exc
            raise DomainError(
                "INGESTION_FEED_ITEM_MATERIALIZATION_INVALID",
                "Feed item materialization failed validation",
                409,
            ) from exc

        if (
            materialization.proposal_id != proposal.id
            or materialization.review_decision_id != review.id
            or materialization.target_kind != _TARGET_KIND
        ):
            raise DomainError(
                "INGESTION_FEED_ITEM_MATERIALIZATION_CONFLICT",
                "Feed item materialization result violates the command contract",
                409,
            )
        return materialization


__all__ = ["SecuredFeedItemMaterializationService"]
