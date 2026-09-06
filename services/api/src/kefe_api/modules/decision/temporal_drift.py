from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class DriftNature(StrEnum):
    STABLE_CONVICTION = "STABLE_CONVICTION"
    MATURED_REVISION = "MATURED_REVISION"
    EXPLORATORY_SHIFT = "EXPLORATORY_SHIFT"
    REINFORCED_CERTAINTY = "REINFORCED_CERTAINTY"


@dataclass(frozen=True, slots=True)
class TemporalDriftResult:
    case_version_id: UUID
    initial_option_code: str
    retest_option_code: str
    time_elapsed_days: int
    is_shifted: bool
    confidence_delta: float
    drift_nature: DriftNature


class TemporalDriftCalculator:
    @staticmethod
    def calculate_drift(
        *,
        case_version_id: UUID,
        initial_option_code: str,
        retest_option_code: str,
        initial_timestamp: datetime,
        retest_timestamp: datetime,
        initial_confidence: float = 0.5,
        retest_confidence: float = 0.5,
    ) -> TemporalDriftResult:
        delta_days = max(1, (retest_timestamp - initial_timestamp).days)
        is_shifted = (initial_option_code.strip() != retest_option_code.strip())
        conf_delta = round(retest_confidence - initial_confidence, 2)

        if not is_shifted and conf_delta >= 0.2:
            nature = DriftNature.REINFORCED_CERTAINTY
        elif not is_shifted:
            nature = DriftNature.STABLE_CONVICTION
        elif delta_days >= 30:
            nature = DriftNature.MATURED_REVISION
        else:
            nature = DriftNature.EXPLORATORY_SHIFT

        return TemporalDriftResult(
            case_version_id=case_version_id,
            initial_option_code=initial_option_code.strip(),
            retest_option_code=retest_option_code.strip(),
            time_elapsed_days=delta_days,
            is_shifted=is_shifted,
            confidence_delta=conf_delta,
            drift_nature=nature,
        )
