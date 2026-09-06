from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DigitalSovereigntyTier(StrEnum):
    SOVEREIGN_RESIDENCY_ENFORCED = "SOVEREIGN_RESIDENCY_ENFORCED"
    CONTROLLED_EPHEMERAL_COMPUTE = "CONTROLLED_EPHEMERAL_COMPUTE"
    DATA_EXFILTRATION_BREACH_ALERT = "DATA_EXFILTRATION_BREACH_ALERT"


@dataclass(frozen=True, slots=True)
class DigitalSovereigntyResult:
    vault_id: str
    jurisdiction_region: str
    sovereignty_tier: DigitalSovereigntyTier
    local_residency_pct: float
    exfiltration_threat_score: float


class DigitalSovereigntyVaultService:
    @staticmethod
    def audit_sovereignty(
        *,
        vault_id: str,
        jurisdiction_region: str,
        local_residency_pct: float,
        exfiltration_threat_score: float,
    ) -> DigitalSovereigntyResult:
        if not 0.0 <= local_residency_pct <= 1.0:
            raise ValueError(f"local_residency_pct must be in [0.0, 1.0], got {local_residency_pct}")
        if not 0.0 <= exfiltration_threat_score <= 1.0:
            raise ValueError(f"exfiltration_threat_score must be in [0.0, 1.0], got {exfiltration_threat_score}")
        if len(jurisdiction_region.strip()) < 2:
            raise ValueError("jurisdiction_region must have at least 2 characters")

        if local_residency_pct >= 0.99 and exfiltration_threat_score <= 0.05:
            tier = DigitalSovereigntyTier.SOVEREIGN_RESIDENCY_ENFORCED
        elif exfiltration_threat_score <= 0.35:
            tier = DigitalSovereigntyTier.CONTROLLED_EPHEMERAL_COMPUTE
        else:
            tier = DigitalSovereigntyTier.DATA_EXFILTRATION_BREACH_ALERT

        return DigitalSovereigntyResult(
            vault_id=vault_id.strip(),
            jurisdiction_region=jurisdiction_region.strip(),
            sovereignty_tier=tier,
            local_residency_pct=round(local_residency_pct, 2),
            exfiltration_threat_score=round(exfiltration_threat_score, 2),
        )
