from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SensitivityCurvePoint:
    parameter_value: float
    acceptance_rate: float

    def to_dict(self) -> dict[str, float]:
        return {
            "parameter_value": self.parameter_value,
            "acceptance_rate": self.acceptance_rate,
        }


@dataclass(frozen=True, slots=True)
class ThresholdAnalysisResult:
    case_version_id: UUID
    parameter_name: str
    unit: str
    tipping_point_threshold: float
    curve_points: tuple[SensitivityCurvePoint, ...]

    def to_dict(self) -> dict[str, any]:
        return {
            "case_version_id": str(self.case_version_id),
            "parameter_name": self.parameter_name,
            "unit": self.unit,
            "tipping_point_threshold": round(self.tipping_point_threshold, 4),
            "curve_points": [p.to_dict() for p in self.curve_points],
        }


class ThresholdSensitivityCalculator:
    @classmethod
    def compute_for_case(cls, case_version_id: UUID) -> ThresholdAnalysisResult:
        """Deterministic sensitivity curve and tipping point for a case."""
        raw_points = [
            (5.0, 0.90),
            (10.0, 0.75),
            (20.0, 0.45),
            (50.0, 0.15),
        ]
        return cls.calculate_sensitivity(
            case_version_id=case_version_id,
            parameter_name="Aylık Ulaşım Katkı Payı / Eşik",
            unit="TL",
            raw_points=raw_points,
        )

    @staticmethod
    def calculate_sensitivity(
        case_version_id: UUID,
        parameter_name: str,
        unit: str,
        raw_points: list[tuple[float, float]],
    ) -> ThresholdAnalysisResult:
        if not raw_points:
            raise ValueError("raw_points must not be empty")

        sorted_points = sorted(raw_points, key=lambda p: p[0])
        curve_points: list[SensitivityCurvePoint] = []
        tipping_point: float | None = None

        for val, rate in sorted_points:
            clamped_rate = max(0.0, min(1.0, rate))
            curve_points.append(
                SensitivityCurvePoint(
                    parameter_value=float(val),
                    acceptance_rate=round(clamped_rate, 4),
                )
            )
            # Tipping point occurs when acceptance rate crosses 0.50 (50%)
            if tipping_point is None and clamped_rate <= 0.50:
                tipping_point = float(val)

        if tipping_point is None:
            tipping_point = curve_points[-1].parameter_value

        return ThresholdAnalysisResult(
            case_version_id=case_version_id,
            parameter_name=parameter_name.strip(),
            unit=unit.strip(),
            tipping_point_threshold=tipping_point,
            curve_points=tuple(curve_points),
        )

