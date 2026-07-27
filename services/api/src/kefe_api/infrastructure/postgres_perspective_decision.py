from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import text

from kefe_api.infrastructure.postgres_reason_decision import PostgresReasonDecisionRepository
from kefe_api.modules.decision.models import (
    PerspectiveItem,
    PerspectiveModerationState,
    PerspectivePublicationState,
    PerspectiveSourceKind,
)


class PostgresPerspectiveDecisionRepository(PostgresReasonDecisionRepository):
    """Decision adapter including the editorial post-Commit Perspective read model."""

    def get_opposing_perspectives(
        self,
        *,
        case_version_id: UUID,
        question_version_id: UUID,
        viewer_value: Any,
        limit: int,
    ) -> tuple[PerspectiveItem, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        id,
                        case_version_id,
                        question_version_id,
                        target_value,
                        text_body,
                        source_kind,
                        moderation_state,
                        publication_state,
                        editorial_priority,
                        created_at
                    FROM content.perspective_item
                    WHERE case_version_id = :case_version_id
                      AND question_version_id = :question_version_id
                      AND source_kind = 'EDITORIAL_HUMAN'
                      AND moderation_state = 'ALLOWED'
                      AND publication_state = 'PUBLISHED'
                      AND target_value <> CAST(:viewer_value AS jsonb)
                    ORDER BY editorial_priority ASC, created_at ASC, id ASC
                    LIMIT :limit
                    """
                ),
                {
                    "case_version_id": case_version_id,
                    "question_version_id": question_version_id,
                    "viewer_value": json.dumps(viewer_value),
                    "limit": limit,
                },
            ).mappings().all()

        return tuple(
            PerspectiveItem(
                id=row["id"],
                case_version_id=row["case_version_id"],
                question_version_id=row["question_version_id"],
                target_value=row["target_value"],
                text=row["text_body"],
                source_kind=PerspectiveSourceKind(row["source_kind"]),
                moderation_state=PerspectiveModerationState(row["moderation_state"]),
                publication_state=PerspectivePublicationState(row["publication_state"]),
                editorial_priority=row["editorial_priority"],
                created_at=row["created_at"],
            )
            for row in rows
        )
