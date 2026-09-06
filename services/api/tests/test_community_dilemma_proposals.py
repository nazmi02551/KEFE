from __future__ import annotations

from kefe_api.modules.decision.community_dilemma_proposals import (
    CommunityDilemmaProposalResult,
    CommunityDilemmaProposalsService,
    CurationState,
)


def test_community_dilemma_proposals_registers_correctly() -> None:
    r = CommunityDilemmaProposalsService.register_proposal(
        proposal_id="prop_001",
        proposed_title="Yapay Zeka Telif Hakları ve Kamusal Alan",
        proposed_context="Üretken yapay zeka modellerinin eğitiminde kamuya açık sanat eserlerinin kullanımı telif ücretine tabi olmalı mıdır?",
        curation_state=CurationState.COMMUNITY_PEER_REVIEW,
        neutrality_score=0.88,
        supporter_count=42,
    )

    assert isinstance(r, CommunityDilemmaProposalResult)
    assert r.curation_state == CurationState.COMMUNITY_PEER_REVIEW
    assert r.neutrality_score == 0.88
    assert r.supporter_count == 42


def test_community_dilemma_invalid_title() -> None:
    failed = False
    try:
        CommunityDilemmaProposalsService.register_proposal(
            proposal_id="prop_002",
            proposed_title="Kısa",  # < 5
            proposed_context="İkilem bağlam metni en az on karakter olmalıdır.",
        )
    except ValueError:
        failed = True

    assert failed is True
