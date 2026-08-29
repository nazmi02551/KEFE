from __future__ import annotations

from uuid import UUID

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.decision.models import CaseVersion
from kefe_api.modules.decision.service import DecisionService

CASE_ID = UUID("71000000-0000-4000-8000-000000000001")
PREVIOUS_ID = UUID("71000000-0000-4000-8000-000000000002")
CURRENT_ID = UUID("71000000-0000-4000-8000-000000000003")


def _case(*, version_id: UUID, version_no: int, title: str) -> CaseVersion:
    return CaseVersion(
        id=version_id,
        case_id=CASE_ID,
        title=title,
        summary=f"Summary {version_no}",
        base_format="DILEMMA",
        primary_domain="DAILY_LIFE",
        content_risk="L0",
        version_no=version_no,
        questions=(),
    )


def test_memory_history_is_newest_first_and_classifies_exact_current() -> None:
    repository = InMemoryDecisionRepository(
        cases=[
            _case(version_id=PREVIOUS_ID, version_no=1, title="Previous"),
            _case(version_id=CURRENT_ID, version_no=2, title="Current"),
        ],
        reveals=[],
    )

    history = DecisionService(repository).list_public_case_versions(CASE_ID)

    assert [item.case_version_id for item in history] == [CURRENT_ID, PREVIOUS_ID]
    assert [item.classification for item in history] == ["CURRENT", "PREVIOUS"]
    assert [item.version_no for item in history] == [2, 1]
    assert all(item.published_at is None for item in history)


def test_memory_history_unknown_case_fails_closed() -> None:
    service = DecisionService(
        InMemoryDecisionRepository(
            cases=[],
            reveals=[],
        )
    )

    with pytest.raises(DomainError) as caught:
        service.list_public_case_versions(CASE_ID)

    assert caught.value.code == "CASE_NOT_FOUND"
    assert caught.value.status_code == 404
