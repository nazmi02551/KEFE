from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class HistoricalEra(StrEnum):
    ANCIENT_CLASSICAL = "ANCIENT_CLASSICAL"
    INDUSTRIAL_ERA = "INDUSTRIAL_ERA"
    TWENTIETH_CENTURY = "TWENTIETH_CENTURY"
    CONTEMPORARY_CRISIS = "CONTEMPORARY_CRISIS"


@dataclass(frozen=True, slots=True)
class HistoricalRetrospectiveResult:
    retrospective_id: str
    case_version_id: UUID
    historical_era: HistoricalEra
    historical_year: int
    historical_event_name: str
    actual_historical_decision: str
    historical_consequence_summary: str


class HistoricalRetrospectiveEngine:
    @staticmethod
    def evaluate(
        *,
        retrospective_id: str,
        case_version_id: UUID,
        historical_era: HistoricalEra,
        historical_year: int,
        historical_event_name: str,
        actual_historical_decision: str,
        historical_consequence_summary: str,
    ) -> HistoricalRetrospectiveResult:
        if len(historical_event_name.strip()) < 4:
            raise ValueError("historical_event_name must have at least 4 characters")
        if len(actual_historical_decision.strip()) < 4:
            raise ValueError("actual_historical_decision must have at least 4 characters")
        if len(historical_consequence_summary.strip()) < 10:
            raise ValueError("historical_consequence_summary must have at least 10 characters")

        return HistoricalRetrospectiveResult(
            retrospective_id=retrospective_id.strip(),
            case_version_id=case_version_id,
            historical_era=historical_era,
            historical_year=historical_year,
            historical_event_name=historical_event_name.strip(),
            actual_historical_decision=actual_historical_decision.strip(),
            historical_consequence_summary=historical_consequence_summary.strip(),
        )
