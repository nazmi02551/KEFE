from __future__ import annotations

from kefe_api.modules.decision.expert_testimony import (
    EpistemicAuthorityTier,
    ExpertTestimonyItem,
    ExpertTestimonyService,
    TestimonyArchetype,
)


def test_expert_testimony_service_assigns_correct_epistemic_tiers() -> None:
    # 1. Independent Academic Expert (Low COI => High Peer Reviewed)
    t1 = ExpertTestimonyService.register_testimony(
        source_name="Prof. Dr. Ayşe Yılmaz (Boğaziçi Üniv. Çevre Enstitüsü)",
        archetype=TestimonyArchetype.INDEPENDENT_ACADEMIC_EXPERT,
        conflict_of_interest_score=0.05,
        testimony_statement="Akademik ölçümlerimiz yeraltı su havzalarında geri dönülemez ağır metal kirliliği riskini %85 olarak göstermektedir.",
    )
    assert isinstance(t1, ExpertTestimonyItem)
    assert t1.epistemic_authority_tier == EpistemicAuthorityTier.HIGH_PEER_REVIEWED

    # 2. Industry Corporate Stakeholder (High COI => Partisan Special Interest)
    t2 = ExpertTestimonyService.register_testimony(
        source_name="Maden İşletmecileri Derneği Sözcüsü",
        archetype=TestimonyArchetype.INDUSTRY_CORPORATE_STAKEHOLDER,
        conflict_of_interest_score=0.90,
        testimony_statement="Tesisimiz en yüksek çevre standartlarına sahip olup bölgeye 5000 kişilik istihdam sağlayacaktır.",
    )
    assert t2.epistemic_authority_tier == EpistemicAuthorityTier.PARTISAN_SPECIAL_INTEREST


def test_expert_testimony_invalid_coi_score() -> None:
    failed = False
    try:
        ExpertTestimonyService.register_testimony(
            source_name="Uzman",
            archetype=TestimonyArchetype.INDEPENDENT_ACADEMIC_EXPERT,
            conflict_of_interest_score=1.5,  # > 1.0
            testimony_statement="Açıklama metni.",
        )
    except ValueError:
        failed = True

    assert failed is True
