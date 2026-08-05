from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from kefe_api.modules.ingestion_orchestration.models import (
    IngestionRun,
    Proposal,
    ProposalReviewDecision,
)


class ProposalQueueReviewState(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"


@dataclass(frozen=True, slots=True)
class ProposalQueueQuery:
    limit: int
    review_state: ProposalQueueReviewState | None = None
    proposal_kind: str | None = None
    risk_code: str | None = None
    run_id: UUID | None = None
    pipeline_code: str | None = None
    after_created_at: datetime | None = None
    after_proposal_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 101:
            raise ValueError("Proposal queue repository limit must be between 1 and 101")
        if (self.after_created_at is None) != (self.after_proposal_id is None):
            raise ValueError("Proposal queue cursor fields must be provided together")
        for value, field_name in (
            (self.proposal_kind, "proposal_kind"),
            (self.risk_code, "risk_code"),
            (self.pipeline_code, "pipeline_code"),
        ):
            if value is not None and not value.strip():
                raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True)
class ProposalQueueCountQuery:
    review_state: ProposalQueueReviewState | None = None
    proposal_kind: str | None = None
    risk_code: str | None = None
    run_id: UUID | None = None
    pipeline_code: str | None = None

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.proposal_kind, "proposal_kind"),
            (self.risk_code, "risk_code"),
            (self.pipeline_code, "pipeline_code"),
        ):
            if value is not None and not value.strip():
                raise ValueError(f"{field_name} must not be blank")


@dataclass(frozen=True, slots=True)
class ProposalQueueRecord:
    proposal: Proposal
    run: IngestionRun
    review: ProposalReviewDecision | None

    @property
    def review_state(self) -> ProposalQueueReviewState:
        if self.review is None:
            return ProposalQueueReviewState.PENDING
        return ProposalQueueReviewState(self.review.decision.value)
