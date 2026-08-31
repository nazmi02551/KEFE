from __future__ import annotations

from uuid import uuid4

from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.decision.models import (
    CANONICAL_OPT_OUT_RESPONSES,
    CaseVersion,
    Question,
    WeighState,
)
from kefe_api.modules.decision.service import DecisionService


def test_canonical_opt_out_constants() -> None:
    assert "OPT_OUT_INSUFFICIENT_INFO" in CANONICAL_OPT_OUT_RESPONSES
    assert "OPT_OUT_MISSING_OPTIONS" in CANONICAL_OPT_OUT_RESPONSES


def test_single_choice_question_accepts_canonical_opt_outs() -> None:
    repo = InMemoryDecisionRepository(cases=[], reveals=[])
    service = DecisionService(repo)

    question = Question(
        id=uuid4(),
        prompt="Should the policy be enacted?",
        response_type="SINGLE_CHOICE",
        required=True,
        response_schema={"options": ["YES", "NO"]},
        stable_code="policy_enacted",
    )

    assert service._is_valid_response(question, "YES") is True
    assert service._is_valid_response(question, "NO") is True
    assert service._is_valid_response(question, "MAYBE") is False

    # Canonical non-coercive opt-outs
    assert service._is_valid_response(question, "OPT_OUT_INSUFFICIENT_INFO") is True
    assert service._is_valid_response(question, "OPT_OUT_MISSING_OPTIONS") is True


def test_confidence_question_rejects_opt_out_strings() -> None:
    repo = InMemoryDecisionRepository(cases=[], reveals=[])
    service = DecisionService(repo)

    question = Question(
        id=uuid4(),
        prompt="How confident are you?",
        response_type="CONFIDENCE",
        required=True,
        response_schema={"min": 1, "max": 5, "step": 1},
        stable_code="confidence_level",
    )

    assert service._is_valid_response(question, 3) is True
    assert service._is_valid_response(question, "OPT_OUT_INSUFFICIENT_INFO") is False
    assert service._is_valid_response(question, "OPT_OUT_MISSING_OPTIONS") is False
