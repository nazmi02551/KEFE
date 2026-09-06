from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EmergencySafeguardStatus(StrEnum):
    PROPORTIONATE_SUNSET_BOUNDED = "PROPORTIONATE_SUNSET_BOUNDED"
    SUNSET_EXPIRATION_APPROACHING = "SUNSET_EXPIRATION_APPROACHING"
    AUTHORITARIAN_CREEP_VIOLATION = "AUTHORITARIAN_CREEP_VIOLATION"


@dataclass(frozen=True, slots=True)
class DemocraticEmergencyResult:
    decree_id: str
    emergency_jurisdiction: str
    safeguard_status: EmergencySafeguardStatus
    proportionality_score: float
    remaining_sunset_days: int


class DemocraticEmergencySafeguardService:
    @staticmethod
    def audit_emergency_decree(
        *,
        decree_id: str,
        emergency_jurisdiction: str,
        proportionality_score: float,
        remaining_sunset_days: int,
    ) -> DemocraticEmergencyResult:
        if not 0.0 <= proportionality_score <= 1.0:
            raise ValueError(f"proportionality_score must be in [0.0, 1.0], got {proportionality_score}")
        if remaining_sunset_days < 0:
            raise ValueError("remaining_sunset_days cannot be negative")
        if len(emergency_jurisdiction.strip()) < 3:
            raise ValueError("emergency_jurisdiction must have at least 3 characters")

        if proportionality_score >= 0.80 and remaining_sunset_days > 15:
            status = EmergencySafeguardStatus.PROPORTIONATE_SUNSET_BOUNDED
        elif remaining_sunset_days <= 15 and proportionality_score >= 0.50:
            status = EmergencySafeguardStatus.SUNSET_EXPIRATION_APPROACHING
        else:
            status = EmergencySafeguardStatus.AUTHORITARIAN_CREEP_VIOLATION

        return DemocraticEmergencyResult(
            decree_id=decree_id.strip(),
            emergency_jurisdiction=emergency_jurisdiction.strip(),
            safeguard_status=status,
            proportionality_score=round(proportionality_score, 2),
            remaining_sunset_days=remaining_sunset_days,
        )
