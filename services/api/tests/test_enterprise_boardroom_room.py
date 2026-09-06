from __future__ import annotations

from kefe_api.modules.decision.enterprise_boardroom_room import (
    BoardroomDilemmaScope,
    EnterpriseBoardroomResult,
    EnterpriseBoardroomService,
)


def test_enterprise_boardroom_evaluates_consensus() -> None:
    r = EnterpriseBoardroomService.evaluate_board_decision(
        room_id="room_ent_001",
        organization_name="Global Tech Ventures A.Ş.",
        dilemma_scope=BoardroomDilemmaScope.ESG_AND_SUSTAINABILITY,
        board_member_count=9,
        votes_in_favor=7,  # 7/9 = 0.777 -> 0.78
        esg_alignment_score=0.92,
    )

    assert isinstance(r, EnterpriseBoardroomResult)
    assert r.dilemma_scope == BoardroomDilemmaScope.ESG_AND_SUSTAINABILITY
    assert r.fiduciary_consensus_ratio == 0.78
    assert r.esg_alignment_score == 0.92


def test_enterprise_boardroom_invalid_votes() -> None:
    failed = False
    try:
        EnterpriseBoardroomService.evaluate_board_decision(
            room_id="room_ent_002",
            organization_name="AB",  # < 3
            dilemma_scope=BoardroomDilemmaScope.CRISIS_MANAGEMENT,
            board_member_count=5,
            votes_in_favor=6,  # > total
            esg_alignment_score=0.50,
        )
    except ValueError:
        failed = True

    assert failed is True
