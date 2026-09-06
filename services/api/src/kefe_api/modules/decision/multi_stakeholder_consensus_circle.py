from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ConsensusCircleState(StrEnum):
    STAKEHOLDER_DIAMETRIC_IMPASSE = "STAKEHOLDER_DIAMETRIC_IMPASSE"
    INTERMEDIATE_CONCESSION_BARGAINING = "INTERMEDIATE_CONCESSION_BARGAINING"
    SYNTHESIS_PACT_RATIFIED = "SYNTHESIS_PACT_RATIFIED"


@dataclass(frozen=True, slots=True)
class ConsensusCircleResult:
    circle_id: str
    pact_title: str
    state: ConsensusCircleState
    stakeholder_groups_count: int
    mutual_concession_score: float
    synthesis_covenant_summary: str


class MultiStakeholderConsensusCircleService:
    @staticmethod
    def register_circle(
        *,
        circle_id: str,
        pact_title: str,
        stakeholder_groups_count: int,
        mutual_concession_score: float,
        synthesis_covenant_summary: str,
    ) -> ConsensusCircleResult:
        if len(pact_title.strip()) < 5:
            raise ValueError("pact_title must have at least 5 characters")
        if stakeholder_groups_count < 2:
            raise ValueError(f"stakeholder_groups_count must be at least 2, got {stakeholder_groups_count}")
        if not 0.0 <= mutual_concession_score <= 1.0:
            raise ValueError(f"mutual_concession_score must be in [0.0, 1.0], got {mutual_concession_score}")
        if len(synthesis_covenant_summary.strip()) < 10:
            raise ValueError("synthesis_covenant_summary must have at least 10 characters")

        if mutual_concession_score >= 0.80:
            state = ConsensusCircleState.SYNTHESIS_PACT_RATIFIED
        elif mutual_concession_score >= 0.40:
            state = ConsensusCircleState.INTERMEDIATE_CONCESSION_BARGAINING
        else:
            state = ConsensusCircleState.STAKEHOLDER_DIAMETRIC_IMPASSE

        return ConsensusCircleResult(
            circle_id=circle_id.strip(),
            pact_title=pact_title.strip(),
            state=state,
            stakeholder_groups_count=stakeholder_groups_count,
            mutual_concession_score=round(mutual_concession_score, 2),
            synthesis_covenant_summary=synthesis_covenant_summary.strip(),
        )
