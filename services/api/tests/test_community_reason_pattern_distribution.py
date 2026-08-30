from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from kefe_api.modules.community_reason.in_memory import (
    InMemoryCommunityReasonRepository,
)
from kefe_api.modules.community_reason.models import (
    CommunityReason,
    CommunityReasonModeration,
)


def _reason(
    *,
    case_version_id,
    tags: tuple[str, ...],
    state: CommunityReasonModeration,
    created_at: datetime,
) -> CommunityReason:
    return CommunityReason(
        id=uuid4(),
        actor_id=uuid4(),
        session_id=uuid4(),
        case_version_id=case_version_id,
        tags=tags,
        body=None,
        moderation_state=state,
        created_at=created_at,
        updated_at=created_at,
    )


def test_pattern_counts_cover_the_full_readable_population_not_the_item_window() -> None:
    repository = InMemoryCommunityReasonRepository()
    case_version_id = uuid4()
    now = datetime.now(UTC)
    older = _reason(
        case_version_id=case_version_id,
        tags=("FAIRNESS", "FAIRNESS", "NEED"),
        state=CommunityReasonModeration.NOT_REQUIRED,
        created_at=now - timedelta(minutes=2),
    )
    latest = _reason(
        case_version_id=case_version_id,
        tags=("RULES",),
        state=CommunityReasonModeration.ALLOWED,
        created_at=now - timedelta(minutes=1),
    )
    pending = _reason(
        case_version_id=case_version_id,
        tags=("HIDDEN_PENDING",),
        state=CommunityReasonModeration.PENDING,
        created_at=now,
    )
    blocked = _reason(
        case_version_id=case_version_id,
        tags=("HIDDEN_BLOCKED",),
        state=CommunityReasonModeration.BLOCKED,
        created_at=now,
    )
    for reason in (older, latest, pending, blocked):
        repository.create_or_replace(reason)

    snapshot = repository.public_snapshot(case_version_id, limit=1)

    assert [item.id for item in snapshot.reasons] == [latest.id]
    assert snapshot.sample_size == 2
    assert dict(snapshot.tag_pattern_counts) == {
        "FAIRNESS": 1,
        "NEED": 1,
        "RULES": 1,
    }

