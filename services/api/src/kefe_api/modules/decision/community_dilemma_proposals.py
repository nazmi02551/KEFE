from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CurationState(StrEnum):
    DRAFT_SUBMITTED = "DRAFT_SUBMITTED"
    COMMUNITY_PEER_REVIEW = "COMMUNITY_PEER_REVIEW"
    EDITORIAL_APPROVED = "EDITORIAL_APPROVED"
    REJECTED_WITH_REASON = "REJECTED_WITH_REASON"


@dataclass(frozen=True, slots=True)
class CommunityDilemmaProposalResult:
    proposal_id: str
    proposed_title: str
    proposed_context: str
    curation_state: CurationState
    neutrality_score: float
    supporter_count: int


class CommunityDilemmaProposalsService:
    @staticmethod
    def register_proposal(
        *,
        proposal_id: str,
        proposed_title: str,
        proposed_context: str,
        curation_state: CurationState = CurationState.DRAFT_SUBMITTED,
        neutrality_score: float = 0.50,
        supporter_count: int = 0,
    ) -> CommunityDilemmaProposalResult:
        if len(proposed_title.strip()) < 5:
            raise ValueError("proposed_title must have at least 5 characters")
        if len(proposed_context.strip()) < 10:
            raise ValueError("proposed_context must have at least 10 characters")
        if not 0.0 <= neutrality_score <= 1.0:
            raise ValueError(f"neutrality_score must be in [0.0, 1.0], got {neutrality_score}")
        if supporter_count < 0:
            raise ValueError("supporter_count cannot be negative")

        return CommunityDilemmaProposalResult(
            proposal_id=proposal_id.strip(),
            proposed_title=proposed_title.strip(),
            proposed_context=proposed_context.strip(),
            curation_state=curation_state,
            neutrality_score=round(neutrality_score, 2),
            supporter_count=supporter_count,
        )
