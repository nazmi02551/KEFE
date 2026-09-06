from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class MigrationEpochType(StrEnum):
    INITIAL_BLIND_RESONANCE = "INITIAL_BLIND_RESONANCE"
    MID_DELIBERATION_SHIFT = "MID_DELIBERATION_SHIFT"
    MATURED_CONSENSUS_STATE = "MATURED_CONSENSUS_STATE"


@dataclass(frozen=True, slots=True)
class TemporalOpinionFlowResult:
    flow_id: str
    case_version_id: UUID
    epoch_type: MigrationEpochType
    option_a_share: float
    option_b_share: float
    undecided_bridge_share: float
    migration_rate: float


class TemporalOpinionFlowCalculator:
    @staticmethod
    def calculate_flow(
        *,
        flow_id: str,
        case_version_id: UUID,
        epoch_type: MigrationEpochType,
        option_a_share: float,
        option_b_share: float,
        undecided_bridge_share: float,
        migration_rate: float,
    ) -> TemporalOpinionFlowResult:
        shares = [option_a_share, option_b_share, undecided_bridge_share]
        for s in shares:
            if not 0.0 <= s <= 1.0:
                raise ValueError(f"Share must be in [0.0, 1.0], got {s}")
        if not 0.0 <= migration_rate <= 1.0:
            raise ValueError(f"migration_rate must be in [0.0, 1.0], got {migration_rate}")

        return TemporalOpinionFlowResult(
            flow_id=flow_id.strip(),
            case_version_id=case_version_id,
            epoch_type=epoch_type,
            option_a_share=round(option_a_share, 2),
            option_b_share=round(option_b_share, 2),
            undecided_bridge_share=round(undecided_bridge_share, 2),
            migration_rate=round(migration_rate, 2),
        )
