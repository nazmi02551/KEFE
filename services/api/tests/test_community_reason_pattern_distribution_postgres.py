from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from kefe_api.core.settings import get_settings
from kefe_api.infrastructure.postgres_community_reason import (
    PostgresCommunityReasonRepository,
)
from kefe_api.main import create_app
from kefe_api.modules.community_reason.models import (
    CommunityReason,
    CommunityReasonModeration,
)
from kefe_api.modules.decision.bootstrap import DEMO_CASE_ID, DEMO_CASE_VERSION_ID

pytestmark = pytest.mark.skipif(
    os.getenv("KEFE_RUN_POSTGRES_TESTS") != "1",
    reason="PostgreSQL integration tests are opt-in",
)


def _actor_and_session(client: TestClient) -> tuple[UUID, UUID]:
    guest = client.post("/v1/identity/guest")
    assert guest.status_code == 201
    headers = {"Authorization": f"Bearer {guest.json()['access_token']}"}
    session = client.post(
        f"/v1/cases/{DEMO_CASE_ID}/weigh-sessions",
        headers=headers,
    )
    assert session.status_code == 201
    return UUID(guest.json()["actor_id"]), UUID(session.json()["session_id"])


def test_postgres_pattern_counts_cover_rows_older_than_the_item_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("KEFE_PERSISTENCE_BACKEND", "postgres")
    get_settings.cache_clear()
    app = create_app()
    client = TestClient(app)
    repository = app.state.community_reason_repository
    assert isinstance(repository, PostgresCommunityReasonRepository)
    now = datetime.now(UTC)
    old_tag = f"CAP032_OLD_{uuid4().hex}"
    new_tag = f"CAP032_NEW_{uuid4().hex}"
    older_actor, older_session = _actor_and_session(client)
    latest_actor, latest_session = _actor_and_session(client)
    older = CommunityReason(
        id=uuid4(),
        actor_id=older_actor,
        session_id=older_session,
        case_version_id=DEMO_CASE_VERSION_ID,
        tags=(old_tag, old_tag),
        body=None,
        moderation_state=CommunityReasonModeration.NOT_REQUIRED,
        created_at=now - timedelta(minutes=2),
        updated_at=now - timedelta(minutes=2),
    )
    latest = CommunityReason(
        id=uuid4(),
        actor_id=latest_actor,
        session_id=latest_session,
        case_version_id=DEMO_CASE_VERSION_ID,
        tags=(new_tag,),
        body=None,
        moderation_state=CommunityReasonModeration.ALLOWED,
        created_at=now - timedelta(minutes=1),
        updated_at=now - timedelta(minutes=1),
    )
    repository.create_or_replace(older)
    repository.create_or_replace(latest)

    try:
        snapshot = repository.public_snapshot(DEMO_CASE_VERSION_ID, limit=1)
        assert [item.id for item in snapshot.reasons] == [latest.id]
        assert snapshot.tag_pattern_counts[old_tag] == 1
        assert snapshot.tag_pattern_counts[new_tag] == 1
        assert snapshot.sample_size >= 2
    finally:
        engine = create_engine(os.environ["KEFE_DATABASE_URL"])
        with engine.begin() as connection:
            connection.execute(
                text("DELETE FROM community.reason WHERE id IN (:older, :latest)"),
                {"older": older.id, "latest": latest.id},
            )
        get_settings.cache_clear()
