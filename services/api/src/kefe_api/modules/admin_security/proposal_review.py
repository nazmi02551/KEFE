from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.admin_security.models import AdminCapability, AdminPrincipal
from kefe_api.modules.admin_security.service import AdminSecurityService
from kefe_api.modules.ingestion_orchestration.models import (
    Proposal,
    ProposalReviewDecision,
    ProposalReviewDecisionKind,
)
from kefe_api.modules.ingestion_orchestration.ports import (
    IngestionOrchestrationRepository,
)
from kefe_api.modules.ingestion_orchestration.service import (
    IngestionOrchestrationService,
)


class SecuredProposalReviewService:
    def __init__(
        self,
        *,
        repository: IngestionOrchestrationRepository,
        orchestration: IngestionOrchestrationService,
        security: AdminSecurityService,
    ) -> None:
        self._repository = repository
        self._orchestration = orchestration
        self._security = security

    def list_pending(
        self,
        principal: AdminPrincipal,
        *,
        proposal_kind: str | None = None,
        limit: int = 50,
        now: datetime | None = None,
    ) -> tuple[Proposal, ...]:
        self._security.authorize(
            principal,
            AdminCapability.PROPOSAL_REVIEW,
            now=now,
        )
        if proposal_kind is not None and not proposal_kind.strip():
            raise DomainError(
                "PROPOSAL_REVIEW_FILTER_INVALID",
                "Proposal kind filter must not be blank",
                422,
            )
        if not 1 <= limit <= 100:
            raise DomainError(
                "PROPOSAL_REVIEW_LIMIT_INVALID",
                "Review queue limit must be between 1 and 100",
                422,
            )
        return self._repository.list_pending_proposals(
            proposal_kind=proposal_kind,
            limit=limit,
        )

    def get(
        self,
        principal: AdminPrincipal,
        proposal_id: UUID,
        *,
        now: datetime | None = None,
    ) -> tuple[Proposal, ProposalReviewDecision | None]:
        self._security.authorize(
            principal,
            AdminCapability.PROPOSAL_REVIEW,
            now=now,
        )
        proposal = self._repository.get_proposal(proposal_id)
        if proposal is None:
            raise DomainError(
                "PROPOSAL_REVIEW_PROPOSAL_NOT_FOUND",
                "Proposal not found",
                404,
            )
        return proposal, self._repository.get_review_decision(proposal_id)

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
            AdminCapability.PROPOSAL_REVIEW,
            now=now,
        )
        if self._repository.get_proposal(proposal_id) is None:
            raise DomainError(
                "PROPOSAL_REVIEW_PROPOSAL_NOT_FOUND",
                "Proposal not found",
                404,
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
        except ValueError as exc:
            existing = self._repository.get_review_decision(proposal_id)
            raise DomainError(
                "PROPOSAL_REVIEW_ALREADY_DECIDED",
                "Proposal already has an immutable terminal review decision",
                409,
                detail=str(exc),
                meta={
                    "review_decision_id": str(existing.id) if existing else None,
                    "decision": existing.decision.value if existing else None,
                },
            ) from exc
