from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class JurisprudentialConsistencyStatus(StrEnum):
    PRECEDENT_ALIGNED_CONSISTENT = "PRECEDENT_ALIGNED_CONSISTENT"
    DISCRETIONARY_DEVIATION_NOTICED = "DISCRETIONARY_DEVIATION_NOTICED"
    EXECUTIVE_INTERFERENCE_SUSPECTED = "EXECUTIVE_INTERFERENCE_SUSPECTED"


@dataclass(frozen=True, slots=True)
class JudicialConsistencyResult:
    chamber_id: str
    court_jurisdiction: str
    case_category: str
    consistency_status: JurisprudentialConsistencyStatus
    precedent_fidelity_score: float
    evaluated_precedent_cases_count: int


class JudicialIndependenceConsistencyService:
    @staticmethod
    def evaluate_consistency(
        *,
        chamber_id: str,
        court_jurisdiction: str,
        case_category: str,
        precedent_fidelity_score: float,
        evaluated_precedent_cases_count: int,
    ) -> JudicialConsistencyResult:
        if not 0.0 <= precedent_fidelity_score <= 1.0:
            raise ValueError(f"precedent_fidelity_score must be in [0.0, 1.0], got {precedent_fidelity_score}")
        if evaluated_precedent_cases_count < 1:
            raise ValueError("evaluated_precedent_cases_count must be at least 1")
        if len(court_jurisdiction.strip()) < 3:
            raise ValueError("court_jurisdiction must have at least 3 characters")
        if len(case_category.strip()) < 4:
            raise ValueError("case_category must have at least 4 characters")

        if precedent_fidelity_score >= 0.85:
            status = JurisprudentialConsistencyStatus.PRECEDENT_ALIGNED_CONSISTENT
        elif precedent_fidelity_score >= 0.50:
            status = JurisprudentialConsistencyStatus.DISCRETIONARY_DEVIATION_NOTICED
        else:
            status = JurisprudentialConsistencyStatus.EXECUTIVE_INTERFERENCE_SUSPECTED

        return JudicialConsistencyResult(
            chamber_id=chamber_id.strip(),
            court_jurisdiction=court_jurisdiction.strip(),
            case_category=case_category.strip(),
            consistency_status=status,
            precedent_fidelity_score=round(precedent_fidelity_score, 2),
            evaluated_precedent_cases_count=evaluated_precedent_cases_count,
        )
