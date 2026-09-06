from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.outcome_triangle import (
    OutcomeTriangleCalculator,
    OutcomeTriangleResult,
    TriangleArchetype,
)


def test_outcome_triangle_calculator_computes_barycentric_weights_and_archetype() -> None:
    case_id = uuid4()

    # 1. Rights Centric (rules=60, empathy=20, utility=20)
    r1 = OutcomeTriangleCalculator.calculate_balance(
        case_version_id=case_id,
        option_code="OPT_LEGAL_STRICT",
        rules_score=60.0,
        empathy_score=20.0,
        utility_score=20.0,
    )
    assert isinstance(r1, OutcomeTriangleResult)
    assert r1.dominant_archetype == TriangleArchetype.RIGHTS_CENTRIC
    assert r1.rules_weight == 0.60
    assert round(r1.rules_weight + r1.empathy_weight + r1.utility_weight, 4) == 1.0

    # 2. Empathy Centric (rules=15, empathy=65, utility=20)
    r2 = OutcomeTriangleCalculator.calculate_balance(
        case_version_id=case_id,
        option_code="OPT_COMPASSION_FIRST",
        rules_score=15.0,
        empathy_score=65.0,
        utility_score=20.0,
    )
    assert r2.dominant_archetype == TriangleArchetype.EMPATHY_CENTRIC

    # 3. Tri-Balanced Harmony (rules=35, empathy=35, utility=30)
    r3 = OutcomeTriangleCalculator.calculate_balance(
        case_version_id=case_id,
        option_code="OPT_HARMONIOUS_SYNTHESIS",
        rules_score=35.0,
        empathy_score=35.0,
        utility_score=30.0,
    )
    assert r3.dominant_archetype == TriangleArchetype.TRI_BALANCED_HARMONY
