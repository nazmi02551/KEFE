from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.content_authoring.models import (
    AuthoringCaseVersion,
    CaseIdentity,
    LifecycleAuditEntry,
)
from kefe_api.modules.editorial_projection.models import (
    EditorialProjectionProfile,
    EditorialProjectionRecord,
    ReviewedProposalBundle,
)


class ReviewedProposalSource(Protocol):
    def get_bundle(
        self,
        candidate_proposal_id: UUID,
        proposal_review_decision_id: UUID,
    ) -> ReviewedProposalBundle | None: ...


class EditorialProjectionProfileRegistry(Protocol):
    def get(
        self,
        profile_code: str,
        profile_version: int,
    ) -> EditorialProjectionProfile | None: ...


class EditorialProjectionRepository(Protocol):
    def get_by_idempotency(
        self,
        candidate_proposal_id: UUID,
        idempotency_key: str,
    ) -> EditorialProjectionRecord | None: ...

    def get_by_candidate(
        self,
        candidate_proposal_id: UUID,
    ) -> EditorialProjectionRecord | None: ...

    def create_atomically(
        self,
        *,
        identity: CaseIdentity,
        initial_version: AuthoringCaseVersion,
        audit: LifecycleAuditEntry,
        record: EditorialProjectionRecord,
    ) -> None: ...
