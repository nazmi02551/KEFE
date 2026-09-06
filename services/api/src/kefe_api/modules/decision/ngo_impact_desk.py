from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class NgoAdvocacyDomain(StrEnum):
    HUMAN_RIGHTS_AND_JUSTICE = "HUMAN_RIGHTS_AND_JUSTICE"
    ENVIRONMENT_AND_CLIMATE = "ENVIRONMENT_AND_CLIMATE"
    PUBLIC_HEALTH_AND_SAFETY = "PUBLIC_HEALTH_AND_SAFETY"
    TRANSPARENCY_AND_ANTI_CORRUPTION = "TRANSPARENCY_AND_ANTI_CORRUPTION"


@dataclass(frozen=True, slots=True)
class NgoImpactDeskResult:
    campaign_id: str
    ngo_name: str
    advocacy_domain: NgoAdvocacyDomain
    citizen_endorsement_count: int
    institutional_reforms_achieved: int
    advocacy_efficacy_score: float


class NgoImpactDeskService:
    @staticmethod
    def evaluate_campaign(
        *,
        campaign_id: str,
        ngo_name: str,
        advocacy_domain: NgoAdvocacyDomain,
        citizen_endorsement_count: int,
        institutional_reforms_achieved: int,
    ) -> NgoImpactDeskResult:
        if len(ngo_name.strip()) < 3:
            raise ValueError("ngo_name must have at least 3 characters")
        if citizen_endorsement_count < 0:
            raise ValueError("citizen_endorsement_count cannot be negative")
        if institutional_reforms_achieved < 0:
            raise ValueError("institutional_reforms_achieved cannot be negative")

        endorsement_score = min(0.50, citizen_endorsement_count / 1000.0 * 0.50)
        reforms_score = min(0.50, institutional_reforms_achieved * 0.15)
        efficacy = endorsement_score + reforms_score
        efficacy = max(0.0, min(1.0, efficacy))

        return NgoImpactDeskResult(
            campaign_id=campaign_id.strip(),
            ngo_name=ngo_name.strip(),
            advocacy_domain=advocacy_domain,
            citizen_endorsement_count=citizen_endorsement_count,
            institutional_reforms_achieved=institutional_reforms_achieved,
            advocacy_efficacy_score=round(efficacy, 2),
        )
