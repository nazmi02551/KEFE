from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class ExplorationMode(StrEnum):
    OBSERVE_ONLY = "OBSERVE_ONLY"
    STUDY_AND_LEARN = "STUDY_AND_LEARN"
    TRANSITION_TO_WEIGH = "TRANSITION_TO_WEIGH"


@dataclass(frozen=True, slots=True)
class ObserveModeSessionResult:
    session_id: str
    case_version_id: UUID
    exploration_mode: ExplorationMode
    is_binding_vote: bool
    viewed_argument_count: int
    viewed_evidence_count: int


class ObserveModeService:
    @staticmethod
    def start_session(
        *,
        session_id: str,
        case_version_id: UUID,
        exploration_mode: ExplorationMode = ExplorationMode.OBSERVE_ONLY,
        viewed_argument_count: int = 0,
        viewed_evidence_count: int = 0,
    ) -> ObserveModeSessionResult:
        if viewed_argument_count < 0:
            raise ValueError("viewed_argument_count cannot be negative")
        if viewed_evidence_count < 0:
            raise ValueError("viewed_evidence_count cannot be negative")
        if len(session_id.strip()) < 4:
            raise ValueError("session_id must have at least 4 characters")

        return ObserveModeSessionResult(
            session_id=session_id.strip(),
            case_version_id=case_version_id,
            exploration_mode=exploration_mode,
            is_binding_vote=False,  # Invariant: Never a binding vote in Observe Mode
            viewed_argument_count=viewed_argument_count,
            viewed_evidence_count=viewed_evidence_count,
        )
