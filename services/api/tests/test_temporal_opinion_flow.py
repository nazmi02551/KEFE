from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.temporal_opinion_flow import (
    MigrationEpochType,
    TemporalOpinionFlowCalculator,
    TemporalOpinionFlowResult,
)


def test_temporal_opinion_flow_calculates_properly() -> None:
    case_id = uuid4()

    r = TemporalOpinionFlowCalculator.calculate_flow(
        flow_id="flw_001",
        case_version_id=case_id,
        epoch_type=MigrationEpochType.MID_DELIBERATION_SHIFT,
        option_a_share=0.45,
        option_b_share=0.35,
        undecided_bridge_share=0.20,
        migration_rate=0.18,
    )

    assert isinstance(r, TemporalOpinionFlowResult)
    assert r.epoch_type == MigrationEpochType.MID_DELIBERATION_SHIFT
    assert r.migration_rate == 0.18


def test_temporal_flow_invalid_share() -> None:
    case_id = uuid4()
    failed = False
    try:
        TemporalOpinionFlowCalculator.calculate_flow(
            flow_id="flw_002",
            case_version_id=case_id,
            epoch_type=MigrationEpochType.INITIAL_BLIND_RESONANCE,
            option_a_share=1.20,  # > 1.0
            option_b_share=0.20,
            undecided_bridge_share=0.10,
            migration_rate=0.10,
        )
    except ValueError:
        failed = True

    assert failed is True
