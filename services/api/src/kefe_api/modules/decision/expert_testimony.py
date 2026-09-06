from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4


class TestimonyArchetype(StrEnum):
    __test__ = False
    INDEPENDENT_ACADEMIC_EXPERT = "INDEPENDENT_ACADEMIC_EXPERT"
    GOVERNMENTAL_REGULATORY_BODY = "GOVERNMENTAL_REGULATORY_BODY"
    INDUSTRY_CORPORATE_STAKEHOLDER = "INDUSTRY_CORPORATE_STAKEHOLDER"
    CIVIL_SOCIETY_ADVOCATE = "CIVIL_SOCIETY_ADVOCATE"


class EpistemicAuthorityTier(StrEnum):
    HIGH_PEER_REVIEWED = "HIGH_PEER_REVIEWED"
    OFFICIAL_REGULATORY = "OFFICIAL_REGULATORY"
    PARTISAN_SPECIAL_INTEREST = "PARTISAN_SPECIAL_INTEREST"


@dataclass(frozen=True, slots=True)
class ExpertTestimonyItem:
    testimony_id: UUID
    source_name: str
    archetype: TestimonyArchetype
    conflict_of_interest_score: float
    epistemic_authority_tier: EpistemicAuthorityTier
    testimony_statement: str


class ExpertTestimonyService:
    @staticmethod
    def register_testimony(
        *,
        source_name: str,
        archetype: TestimonyArchetype,
        conflict_of_interest_score: float,
        testimony_statement: str,
    ) -> ExpertTestimonyItem:
        if len(source_name.strip()) < 3:
            raise ValueError("source_name must have at least 3 characters")
        if not 0.0 <= conflict_of_interest_score <= 1.0:
            raise ValueError(f"conflict_of_interest_score must be in [0.0, 1.0], got {conflict_of_interest_score}")
        if len(testimony_statement.strip()) < 10:
            raise ValueError("testimony_statement must have at least 10 characters")

        # Derive epistemic authority tier
        if archetype == TestimonyArchetype.INDEPENDENT_ACADEMIC_EXPERT and conflict_of_interest_score <= 0.20:
            tier = EpistemicAuthorityTier.HIGH_PEER_REVIEWED
        elif archetype == TestimonyArchetype.GOVERNMENTAL_REGULATORY_BODY:
            tier = EpistemicAuthorityTier.OFFICIAL_REGULATORY
        else:
            tier = EpistemicAuthorityTier.PARTISAN_SPECIAL_INTEREST

        return ExpertTestimonyItem(
            testimony_id=uuid4(),
            source_name=source_name.strip(),
            archetype=archetype,
            conflict_of_interest_score=round(conflict_of_interest_score, 2),
            epistemic_authority_tier=tier,
            testimony_statement=testimony_statement.strip(),
        )
