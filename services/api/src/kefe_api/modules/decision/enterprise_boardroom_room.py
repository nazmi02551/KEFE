from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BoardroomDilemmaScope(StrEnum):
    ESG_AND_SUSTAINABILITY = "ESG_AND_SUSTAINABILITY"
    CAPITAL_ALLOCATION_AND_MA = "CAPITAL_ALLOCATION_AND_MA"
    EXECUTIVE_COMPENSATION = "EXECUTIVE_COMPENSATION"
    CRISIS_MANAGEMENT = "CRISIS_MANAGEMENT"


@dataclass(frozen=True, slots=True)
class EnterpriseBoardroomResult:
    room_id: str
    organization_name: str
    dilemma_scope: BoardroomDilemmaScope
    board_member_count: int
    fiduciary_consensus_ratio: float
    esg_alignment_score: float


class EnterpriseBoardroomService:
    @staticmethod
    def evaluate_board_decision(
        *,
        room_id: str,
        organization_name: str,
        dilemma_scope: BoardroomDilemmaScope,
        board_member_count: int,
        votes_in_favor: int,
        esg_alignment_score: float,
    ) -> EnterpriseBoardroomResult:
        if board_member_count < 1:
            raise ValueError("board_member_count must be at least 1")
        if not 0 <= votes_in_favor <= board_member_count:
            raise ValueError(f"votes_in_favor must be in [0, {board_member_count}]")
        if not 0.0 <= esg_alignment_score <= 1.0:
            raise ValueError(f"esg_alignment_score must be in [0.0, 1.0], got {esg_alignment_score}")
        if len(organization_name.strip()) < 3:
            raise ValueError("organization_name must have at least 3 characters")

        consensus_ratio = votes_in_favor / board_member_count

        return EnterpriseBoardroomResult(
            room_id=room_id.strip(),
            organization_name=organization_name.strip(),
            dilemma_scope=dilemma_scope,
            board_member_count=board_member_count,
            fiduciary_consensus_ratio=round(consensus_ratio, 2),
            esg_alignment_score=round(esg_alignment_score, 2),
        )
