from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TransitionStatus(StrEnum):
    COOLING_OFF_COMPLIANT = "COOLING_OFF_COMPLIANT"
    RAPID_REGULATORY_TRANSITION_ALERT = "RAPID_REGULATORY_TRANSITION_ALERT"
    PROVEN_CAPTURE_VULNERABILITY = "PROVEN_CAPTURE_VULNERABILITY"


@dataclass(frozen=True, slots=True)
class RevolvingDoorResult:
    transition_id: str
    official_name_anonymized: str
    status: TransitionStatus
    cooling_off_months_observed: int
    capture_risk_score: float
    regulatory_agency_source: str


class RevolvingDoorMonitorService:
    @staticmethod
    def audit_transition(
        *,
        transition_id: str,
        official_name_anonymized: str,
        cooling_off_months_observed: int,
        capture_risk_score: float,
        regulatory_agency_source: str,
    ) -> RevolvingDoorResult:
        if cooling_off_months_observed < 0:
            raise ValueError("cooling_off_months_observed cannot be negative")
        if not 0.0 <= capture_risk_score <= 1.0:
            raise ValueError(f"capture_risk_score must be in [0.0, 1.0], got {capture_risk_score}")
        if len(regulatory_agency_source.strip()) < 3:
            raise ValueError("regulatory_agency_source must have at least 3 characters")

        if capture_risk_score >= 0.80 or cooling_off_months_observed < 6:
            status = TransitionStatus.PROVEN_CAPTURE_VULNERABILITY
        elif cooling_off_months_observed < 24:
            status = TransitionStatus.RAPID_REGULATORY_TRANSITION_ALERT
        else:
            status = TransitionStatus.COOLING_OFF_COMPLIANT

        return RevolvingDoorResult(
            transition_id=transition_id.strip(),
            official_name_anonymized=official_name_anonymized.strip(),
            status=status,
            cooling_off_months_observed=cooling_off_months_observed,
            capture_risk_score=round(capture_risk_score, 2),
            regulatory_agency_source=regulatory_agency_source.strip(),
        )
