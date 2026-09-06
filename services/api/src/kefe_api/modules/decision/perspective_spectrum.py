from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class PrimaryValueHue(StrEnum):
    SECURITY_AND_ORDER = "SECURITY_AND_ORDER"
    AUTONOMY_AND_LIBERTY = "AUTONOMY_AND_LIBERTY"
    EQUALITY_AND_CARE = "EQUALITY_AND_CARE"
    INNOVATION_AND_PROGRESS = "INNOVATION_AND_PROGRESS"
    TRADITION_AND_HERITAGE = "TRADITION_AND_HERITAGE"


@dataclass(frozen=True, slots=True)
class PerspectiveSpectrumResult:
    spectrum_id: str
    case_version_id: UUID
    primary_value_hue: PrimaryValueHue
    argument_resonance_count: int
    cross_value_bridge_ratio: float
    core_moral_intuition: str


class PerspectiveSpectrumService:
    @staticmethod
    def map_spectrum(
        *,
        spectrum_id: str,
        case_version_id: UUID,
        primary_value_hue: PrimaryValueHue,
        argument_resonance_count: int,
        cross_value_bridge_ratio: float,
        core_moral_intuition: str,
    ) -> PerspectiveSpectrumResult:
        if argument_resonance_count < 0:
            raise ValueError("argument_resonance_count cannot be negative")
        if not 0.0 <= cross_value_bridge_ratio <= 1.0:
            raise ValueError(f"cross_value_bridge_ratio must be in [0.0, 1.0], got {cross_value_bridge_ratio}")
        if len(core_moral_intuition.strip()) < 10:
            raise ValueError("core_moral_intuition must have at least 10 characters")

        return PerspectiveSpectrumResult(
            spectrum_id=spectrum_id.strip(),
            case_version_id=case_version_id,
            primary_value_hue=primary_value_hue,
            argument_resonance_count=argument_resonance_count,
            cross_value_bridge_ratio=round(cross_value_bridge_ratio, 2),
            core_moral_intuition=core_moral_intuition.strip(),
        )
