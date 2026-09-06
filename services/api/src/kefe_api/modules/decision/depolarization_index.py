from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class BridgeEfficacyState(StrEnum):
    HIGH_DEPOLARIZATION = "HIGH_DEPOLARIZATION"
    MODERATE_BRIDGE_RESONANCE = "MODERATE_BRIDGE_RESONANCE"
    PERSISTENT_POLARIZATION = "PERSISTENT_POLARIZATION"


@dataclass(frozen=True, slots=True)
class DepolarizationIndexResult:
    case_version_id: UUID
    pre_deliberation_distance: float
    post_deliberation_distance: float
    depolarization_score: float
    bridge_efficacy_state: BridgeEfficacyState


class DepolarizationCalculator:
    @staticmethod
    def calculate(
        *,
        case_version_id: UUID,
        pre_deliberation_distance: float,
        post_deliberation_distance: float,
    ) -> DepolarizationIndexResult:
        if not 0.0 <= pre_deliberation_distance <= 1.0:
            raise ValueError(f"pre_deliberation_distance must be in [0.0, 1.0], got {pre_deliberation_distance}")
        if not 0.0 <= post_deliberation_distance <= 1.0:
            raise ValueError(f"post_deliberation_distance must be in [0.0, 1.0], got {post_deliberation_distance}")

        # Depolarization score is relative reduction in distance
        if pre_deliberation_distance > 0.0:
            delta = max(0.0, pre_deliberation_distance - post_deliberation_distance)
            score = delta / pre_deliberation_distance
        else:
            score = 1.0

        score = max(0.0, min(1.0, score))

        if score >= 0.50:
            state = BridgeEfficacyState.HIGH_DEPOLARIZATION
        elif score >= 0.20:
            state = BridgeEfficacyState.MODERATE_BRIDGE_RESONANCE
        else:
            state = BridgeEfficacyState.PERSISTENT_POLARIZATION

        return DepolarizationIndexResult(
            case_version_id=case_version_id,
            pre_deliberation_distance=round(pre_deliberation_distance, 2),
            post_deliberation_distance=round(post_deliberation_distance, 2),
            depolarization_score=round(score, 2),
            bridge_efficacy_state=state,
        )
