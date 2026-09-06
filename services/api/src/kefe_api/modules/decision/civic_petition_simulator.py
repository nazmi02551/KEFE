from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PetitionStage(StrEnum):
    DRAFT_IMPACT_SIMULATION = "DRAFT_IMPACT_SIMULATION"
    SIGNATURE_GATHERING_CAMPAIGN = "SIGNATURE_GATHERING_CAMPAIGN"
    SUBMITTED_TO_PARLIAMENT = "SUBMITTED_TO_PARLIAMENT"


@dataclass(frozen=True, slots=True)
class CivicPetitionResult:
    petition_id: str
    bill_title: str
    stage: PetitionStage
    signatures_count: int
    signature_target_threshold: int
    projected_net_benefit_score: float


class CivicPetitionSimulatorService:
    @staticmethod
    def simulate_petition(
        *,
        petition_id: str,
        bill_title: str,
        signatures_count: int,
        signature_target_threshold: int,
        projected_net_benefit_score: float,
    ) -> CivicPetitionResult:
        if len(bill_title.strip()) < 5:
            raise ValueError("bill_title must have at least 5 characters")
        if signatures_count < 0:
            raise ValueError("signatures_count cannot be negative")
        if signature_target_threshold < 1000:
            raise ValueError(f"signature_target_threshold must be >= 1000, got {signature_target_threshold}")
        if not -1.0 <= projected_net_benefit_score <= 1.0:
            raise ValueError(f"projected_net_benefit_score must be in [-1.0, 1.0], got {projected_net_benefit_score}")

        if signatures_count >= signature_target_threshold:
            stage = PetitionStage.SUBMITTED_TO_PARLIAMENT
        elif signatures_count > 0:
            stage = PetitionStage.SIGNATURE_GATHERING_CAMPAIGN
        else:
            stage = PetitionStage.DRAFT_IMPACT_SIMULATION

        return CivicPetitionResult(
            petition_id=petition_id.strip(),
            bill_title=bill_title.strip(),
            stage=stage,
            signatures_count=signatures_count,
            signature_target_threshold=signature_target_threshold,
            projected_net_benefit_score=round(projected_net_benefit_score, 2),
        )
