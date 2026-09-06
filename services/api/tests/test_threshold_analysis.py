from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.threshold_analysis import (
    SensitivityCurvePoint,
    ThresholdAnalysisResult,
    ThresholdSensitivityCalculator,
)


def test_threshold_sensitivity_calculator_identifies_tipping_point() -> None:
    case_id = uuid4()
    raw_points = [
        (5.0, 0.90),   # 90% accept at 5 TL
        (10.0, 0.75),  # 75% accept at 10 TL
        (20.0, 0.45),  # 45% accept at 20 TL (crosses 50% threshold)
        (50.0, 0.15),  # 15% accept at 50 TL
    ]

    result = ThresholdSensitivityCalculator.calculate_sensitivity(
        case_id,
        "Aylık Ulaşım Katkı Payı",
        "TL",
        raw_points,
    )

    assert isinstance(result, ThresholdAnalysisResult)
    assert result.parameter_name == "Aylık Ulaşım Katkı Payı"
    assert result.unit == "TL"
    assert result.tipping_point_threshold == 20.0
    assert len(result.curve_points) == 4
    assert result.curve_points[0].acceptance_rate == 0.90
