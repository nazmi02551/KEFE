from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.ingestion_orchestration.models import (
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)


class SecuredProposalReviewService:
    """Admin facade for one terminal Proposal review decision."""

    def __init__(
        self,
        *,
        orchestration: IngestionOrchestrationService,
        security: AdminSecurityService,
    ) -> None:
        self._orchestration = orchestration
        self._security = security

    def review(
        self,
        principal: AdminPrincipal,
        *,
        proposal_id: UUID,
        decision: ProposalReviewDecisionKind,
        rationale: str | None = None,
        reason_code: str | None = None,
        policy_version: str | None = None,
        risk_policy_version: str | None = None,
        now: datetime | None = None,
    ) -> ProposalReviewDecision:
        self._security.authorize(
            principal,
            AdminCapability.CONTENT_REVIEW,
            now=now,
        )
        try:
            return self._orchestration.review_proposal(
                proposal_id=proposal_id,
                decision=decision,
                reviewer_ref=principal.audit_actor_ref,
                rationale=rationale,
                reason_code=reason_code,
                policy_version=policy_version,
                risk_policy_version=risk_policy_version,
            )
        except KeyError as exc:
            raise DomainError(
                "INGESTION_PROPOSAL_NOT_FOUND",
                "Proposal not found",
                404,
            ) from exc
        except ValueError as exc:
            raise DomainError(
                "INGESTION_PROPOSAL_ALREADY_REVIEWED",
                "Proposal already has a terminal review decision",
                409,
            ) from exc
