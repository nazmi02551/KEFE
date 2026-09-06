from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CognitiveDensityMode(StrEnum):
    STREAMLINED_ESSENTIALS = "STREAMLINED_ESSENTIALS"
    BALANCED_DELIBERATIVE = "BALANCED_DELIBERATIVE"
    SCHOLARLY_EXHAUSTIVE = "SCHOLARLY_EXHAUSTIVE"


@dataclass(frozen=True, slots=True)
class AdaptiveCognitiveLoadResult:
    profile_id: str
    density_mode: CognitiveDensityMode
    reading_time_reduction_pct: float
    comprehension_retention_index: float
    is_fatigue_mitigation_active: bool


class AdaptiveCognitiveLoadService:
    @staticmethod
    def configure_profile(
        *,
        profile_id: str,
        density_mode: CognitiveDensityMode,
        comprehension_retention_index: float = 0.90,
    ) -> AdaptiveCognitiveLoadResult:
        if not 0.0 <= comprehension_retention_index <= 1.0:
            raise ValueError(f"comprehension_retention_index must be in [0.0, 1.0], got {comprehension_retention_index}")

        # Compute reduction percentage based on density mode
        if density_mode == CognitiveDensityMode.STREAMLINED_ESSENTIALS:
            reduction = 0.60
            fatigue_active = True
        elif density_mode == CognitiveDensityMode.BALANCED_DELIBERATIVE:
            reduction = 0.25
            fatigue_active = False
        else:
            reduction = 0.00
            fatigue_active = False

        return AdaptiveCognitiveLoadResult(
            profile_id=profile_id.strip(),
            density_mode=density_mode,
            reading_time_reduction_pct=reduction,
            comprehension_retention_index=round(comprehension_retention_index, 2),
            is_fatigue_mitigation_active=fatigue_active,
        )
