from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CitizenJuryStage(StrEnum):
    STRATIFIED_PANEL_ASSEMBLY = "STRATIFIED_PANEL_ASSEMBLY"
    EXPERT_HEARINGS_IN_SESSION = "EXPERT_HEARINGS_IN_SESSION"
    CONSENSUS_VERDICT_EMITTED = "CONSENSUS_VERDICT_EMITTED"


@dataclass(frozen=True, slots=True)
class CitizenJuryResult:
    jury_id: str
    dilemma_title: str
    stage: CitizenJuryStage
    juror_count: int
    expert_witnesses_count: int
    verdict_consensus_rate: float


class CitizenJuryChamberService:
    @staticmethod
    def convene_jury(
        *,
        jury_id: str,
        dilemma_title: str,
        stage: CitizenJuryStage,
        juror_count: int,
        expert_witnesses_count: int,
        verdict_consensus_rate: float,
    ) -> CitizenJuryResult:
        if len(dilemma_title.strip()) < 5:
            raise ValueError("dilemma_title must have at least 5 characters")
        if juror_count < 12:
            raise ValueError(f"juror_count must be at least 12 for valid sortition, got {juror_count}")
        if expert_witnesses_count < 1:
            raise ValueError("expert_witnesses_count must be at least 1")
        if not 0.0 <= verdict_consensus_rate <= 1.0:
            raise ValueError(f"verdict_consensus_rate must be in [0.0, 1.0], got {verdict_consensus_rate}")

        return CitizenJuryResult(
            jury_id=jury_id.strip(),
            dilemma_title=dilemma_title.strip(),
            stage=stage,
            juror_count=juror_count,
            expert_witnesses_count=expert_witnesses_count,
            verdict_consensus_rate=round(verdict_consensus_rate, 2),
        )
