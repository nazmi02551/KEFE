from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import text

from kefe_api.infrastructure.postgres_explore_decision import PostgresExploreDecisionRepository
from kefe_api.modules.decision.models import (
    DraftUpdateStatus,
    PrivateReason,
    ReasonModerationState,
    ReasonUpdateAttempt,
    WeighState,
)


class PostgresReasonDecisionRepository(PostgresExploreDecisionRepository):
    """Decision adapter including private-by-default reason persistence."""

    def update_private_reason(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        tags: tuple[str, ...],
        text: str | None,
        updated_at: datetime,
    ) -> ReasonUpdateAttempt:
        with self._engine.begin() as connection:
            row = self._lock_session(connection, actor_id=actor_id, session_id=session_id)
            if row is None:
                return ReasonUpdateAttempt(DraftUpdateStatus.NOT_FOUND, None)
            if row["state"] != WeighState.DRAFT.value:
                return ReasonUpdateAttempt(DraftUpdateStatus.NOT_EDITABLE, None)

            moderation_state = (
                ReasonModerationState.PENDING
                if text is not None
                else ReasonModerationState.NOT_REQUIRED
            )
            connection.execute(
                text(
                    """
                    INSERT INTO decision.private_reason (
                        session_id,
                        tags,
                        text_body,
                        moderation_state,
                        visibility,
                        updated_at
                    )
                    VALUES (
                        :session_id,
                        CAST(:tags AS jsonb),
                        :text_body,
                        :moderation_state,
                        'PRIVATE',
                        :updated_at
                    )
                    ON CONFLICT (session_id)
                    DO UPDATE SET
                        tags = EXCLUDED.tags,
                        text_body = EXCLUDED.text_body,
                        moderation_state = EXCLUDED.moderation_state,
                        visibility = 'PRIVATE',
                        updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    "session_id": session_id,
                    "tags": json.dumps(tags),
                    "text_body": text,
                    "moderation_state": moderation_state.value,
                    "updated_at": updated_at,
                },
            )
            connection.execute(
                text(
                    """
                    UPDATE decision.weigh_session
                    SET updated_at = :updated_at
                    WHERE id = :session_id
                    """
                ),
                {"session_id": session_id, "updated_at": updated_at},
            )
            return ReasonUpdateAttempt(
                DraftUpdateStatus.UPDATED,
                PrivateReason(
                    session_id=session_id,
                    tags=tags,
                    text=text,
                    moderation_state=moderation_state,
                    updated_at=updated_at,
                ),
            )
