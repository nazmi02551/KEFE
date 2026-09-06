from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.ethical_vector_space import (
    DominantMoralAttractor,
    EthicalVectorSpaceCalculator,
    EthicalVectorSpaceResult,
)


def test_ethical_vector_space_calculates_dominant() -> None:
    case_id = uuid4()

    r = EthicalVectorSpaceCalculator.calculate_vector(
        case_version_id=case_id,
        utilitarian_score=0.45,
        deontological_score=0.90,  # highest
        communitarian_score=0.60,
        intergenerational_score=0.70,
    )

    assert isinstance(r, EthicalVectorSpaceResult)
    assert r.dominant_attractor == DominantMoralAttractor.DEONTOLOGICAL_RIGHTS
    assert r.deontological_weight == 0.90


def test_ethical_vector_invalid_range() -> None:
    case_id = uuid4()
    failed = False
    try:
        EthicalVectorSpaceCalculator.calculate_vector(
            case_version_id=case_id,
            utilitarian_score=1.20,  # > 1.0
            deontological_score=0.50,
            communitarian_score=0.50,
            intergenerational_score=0.50,
        )
    except ValueError:
        failed = True

    assert failed is True
