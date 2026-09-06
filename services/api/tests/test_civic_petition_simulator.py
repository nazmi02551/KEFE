from __future__ import annotations

from kefe_api.modules.decision.civic_petition_simulator import (
    CivicPetitionResult,
    CivicPetitionSimulatorService,
    PetitionStage,
)


def test_civic_petition_submits_to_parliament() -> None:
    r = CivicPetitionSimulatorService.simulate_petition(
        petition_id="pet_001",
        bill_title="Dönüştürülebilir Ambalaj ve Sıfır Atık Zorunluluğu Kanunu",
        signatures_count=120000,
        signature_target_threshold=100000,
        projected_net_benefit_score=0.78,
    )

    assert isinstance(r, CivicPetitionResult)
    assert r.stage == PetitionStage.SUBMITTED_TO_PARLIAMENT
    assert r.signatures_count == 120000
    assert r.projected_net_benefit_score == 0.78


def test_civic_petition_invalid_threshold() -> None:
    failed = False
    try:
        CivicPetitionSimulatorService.simulate_petition(
            petition_id="pet_002",
            bill_title="Kısa",  # < 5
            signatures_count=-5,  # < 0
            signature_target_threshold=500,  # < 1000
            projected_net_benefit_score=1.50,  # > 1.0
        )
    except ValueError:
        failed = True

    assert failed is True
