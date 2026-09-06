from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.observe_mode_exploration import (
    ExplorationMode,
    ObserveModeService,
    ObserveModeSessionResult,
)


def test_observe_mode_service_creates_non_binding_session() -> None:
    case_id = uuid4()

    r = ObserveModeService.start_session(
        session_id="obs_001",
        case_version_id=case_id,
        exploration_mode=ExplorationMode.STUDY_AND_LEARN,
        viewed_argument_count=6,
        viewed_evidence_count=3,
    )

    assert isinstance(r, ObserveModeSessionResult)
    assert r.is_binding_vote is False
    assert r.exploration_mode == ExplorationMode.STUDY_AND_LEARN
    assert r.viewed_argument_count == 6


def test_observe_mode_invalid_counts() -> None:
    case_id = uuid4()
    failed = False
    try:
        ObserveModeService.start_session(
            session_id="obs_002",
            case_version_id=case_id,
            viewed_argument_count=-1,  # < 0
        )
    except ValueError:
        failed = True

    assert failed is True
