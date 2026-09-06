from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LobbyingExposureLevel(StrEnum):
    CLEAN_INDEPENDENT_DISCLOSURE = "CLEAN_INDEPENDENT_DISCLOSURE"
    DECLARED_STAKEHOLDER_FINANCING = "DECLARED_STAKEHOLDER_FINANCING"
    HIGH_CONFLICT_EXPOSURE_ALERT = "HIGH_CONFLICT_EXPOSURE_ALERT"


@dataclass(frozen=True, slots=True)
class LobbyingRadarResult:
    radar_id: str
    organization_id: str
    exposure_level: LobbyingExposureLevel
    transparency_index: float
    declared_funding_amount_usd: float
    primary_benefactor_sector: str


class ConflictInterestLobbyingRadarService:
    @staticmethod
    def evaluate_organization(
        *,
        radar_id: str,
        organization_id: str,
        transparency_index: float,
        declared_funding_amount_usd: float,
        primary_benefactor_sector: str,
    ) -> LobbyingRadarResult:
        if not 0.0 <= transparency_index <= 1.0:
            raise ValueError(f"transparency_index must be in [0.0, 1.0], got {transparency_index}")
        if declared_funding_amount_usd < 0:
            raise ValueError("declared_funding_amount_usd cannot be negative")
        if len(primary_benefactor_sector.strip()) < 3:
            raise ValueError("primary_benefactor_sector must have at least 3 characters")

        if declared_funding_amount_usd == 0 and transparency_index >= 0.90:
            level = LobbyingExposureLevel.CLEAN_INDEPENDENT_DISCLOSURE
        elif transparency_index >= 0.65:
            level = LobbyingExposureLevel.DECLARED_STAKEHOLDER_FINANCING
        else:
            level = LobbyingExposureLevel.HIGH_CONFLICT_EXPOSURE_ALERT

        return LobbyingRadarResult(
            radar_id=radar_id.strip(),
            organization_id=organization_id.strip(),
            exposure_level=level,
            transparency_index=round(transparency_index, 2),
            declared_funding_amount_usd=round(declared_funding_amount_usd, 2),
            primary_benefactor_sector=primary_benefactor_sector.strip(),
        )
