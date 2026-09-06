from __future__ import annotations

from uuid import uuid4
import pytest

from kefe_api.modules.decision.incentive_map import (
    AlignmentStatusEnum,
    IncentiveMapCalculator,
    IncentiveMapResult,
    IncentiveNodeItem,
    IncentiveTypeEnum,
    PerverseRiskEnum,
)


def test_incentive_map_calculator_valid() -> None:
    case_id = uuid4()
    nodes = [
        IncentiveNodeItem(
            stakeholder_group="Yatırımcılar",
            core_incentive="Getiri maksimizasyonu",
            incentive_type=IncentiveTypeEnum.FINANCIAL_PROFIT,
            alignment_status=AlignmentStatusEnum.MISALIGNED,
            intensity_score=0.8,
            unintended_behavior="Maliyetten kaçınma",
        ),
        IncentiveNodeItem(
            stakeholder_group="Vatandaşlar",
            core_incentive="Temiz çevre ve uygun maliyet",
            incentive_type=IncentiveTypeEnum.CIVIC_PUBLIC_WELFARE,
            alignment_status=AlignmentStatusEnum.ALIGNED,
            intensity_score=0.9,
        ),
    ]

    result = IncentiveMapCalculator.analyze(
        map_id="inc-test-01",
        case_version_id=case_id,
        alignment_index=0.70,
        perverse_incentive_risk=PerverseRiskEnum.LOW,
        primary_driver="Kâr ve Kamu Yararı Dengesi",
        mitigation_mechanism="Şeffaflık zorunluluğu",
        incentive_nodes=nodes,
    )

    assert result.map_id == "inc-test-01"
    assert result.case_version_id == case_id
    assert result.alignment_index == 0.70
    assert result.perverse_incentive_risk == PerverseRiskEnum.LOW
    assert len(result.incentive_nodes) == 2

    d = result.to_dict()
    assert d["map_id"] == "inc-test-01"
    assert d["alignment_index"] == 0.70
    assert len(d["incentive_nodes"]) == 2


def test_incentive_map_validation_errors() -> None:
    case_id = uuid4()
    with pytest.raises(ValueError, match="alignment_index must be in"):
        IncentiveMapCalculator.analyze(
            map_id="i1",
            case_version_id=case_id,
            alignment_index=1.5,
            perverse_incentive_risk=PerverseRiskEnum.HIGH,
            primary_driver="Dürtü",
            mitigation_mechanism="Çözüm",
            incentive_nodes=[
                IncentiveNodeItem(
                    "Grup", "Teşvik", IncentiveTypeEnum.FINANCIAL_PROFIT, AlignmentStatusEnum.ALIGNED, 0.5
                )
            ],
        )

    with pytest.raises(ValueError, match="primary_driver must have at least 3 characters"):
        IncentiveMapCalculator.analyze(
            map_id="i1",
            case_version_id=case_id,
            alignment_index=0.5,
            perverse_incentive_risk=PerverseRiskEnum.HIGH,
            primary_driver="D",
            mitigation_mechanism="Çözüm",
            incentive_nodes=[
                IncentiveNodeItem(
                    "Grup", "Teşvik", IncentiveTypeEnum.FINANCIAL_PROFIT, AlignmentStatusEnum.ALIGNED, 0.5
                )
            ],
        )


def test_incentive_map_compute_for_case() -> None:
    case_id = uuid4()
    result = IncentiveMapCalculator.compute_for_case(case_id)
    assert result.case_version_id == case_id
    assert 0.0 <= result.alignment_index <= 1.0
    assert len(result.incentive_nodes) >= 3
    assert result.perverse_incentive_risk in [e for e in PerverseRiskEnum]
