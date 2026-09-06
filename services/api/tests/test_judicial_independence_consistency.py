from __future__ import annotations

from kefe_api.modules.decision.judicial_independence_consistency import (
    JudicialConsistencyResult,
    JudicialIndependenceConsistencyService,
    JurisprudentialConsistencyStatus,
)


def test_judicial_evaluates_precedent_consistency() -> None:
    r = JudicialIndependenceConsistencyService.evaluate_consistency(
        chamber_id="jdc_001",
        court_jurisdiction="Danıştay 6. Dairesi",
        case_category="Kentsel Dönüşüm ve Mülkiyet Hakkı",
        precedent_fidelity_score=0.92,
        evaluated_precedent_cases_count=48,
    )

    assert isinstance(r, JudicialConsistencyResult)
    assert r.consistency_status == JurisprudentialConsistencyStatus.PRECEDENT_ALIGNED_CONSISTENT
    assert r.precedent_fidelity_score == 0.92
    assert r.evaluated_precedent_cases_count == 48


def test_judicial_invalid_inputs() -> None:
    failed = False
    try:
        JudicialIndependenceConsistencyService.evaluate_consistency(
            chamber_id="jdc_002",
            court_jurisdiction="AB",  # < 3
            case_category="Kı",  # < 4
            precedent_fidelity_score=1.50,  # > 1.0
            evaluated_precedent_cases_count=0,  # < 1
        )
    except ValueError:
        failed = True

    assert failed is True
