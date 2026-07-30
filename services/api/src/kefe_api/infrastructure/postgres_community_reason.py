from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from types import MappingProxyType
from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.community_reason.models import (
    CommunityReason,
    CommunityReasonModeration,
    CommunityReasonSnapshot,
    PublicCommunityReason,
    ReasonReaction,
    ReasonReportCode,
)


class PostgresCommunityReasonRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_or_replace(self, reason: CommunityReason) -> CommunityReason:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    INSERT INTO community.reason (
                        id, actor_id, session_id, case_version_id, tags, body,
                        moderation_state, created_at, updated_at
                    ) VALUES (
                        :id, :actor_id, :session_id, :case_version_id,
                        CAST(:tags AS jsonb), :body, :moderation_state,
                        :created_at, :updated_at
                    )
                    ON CONFLICT (actor_id, session_id) DO UPDATE SET
                        tags = EXCLUDED.tags,
                        body = EXCLUDED.body,
                        moderation_state = EXCLUDED.moderation_state,
                        updated_at = EXCLUDED.updated_at
                    RETURNING id, actor_id, session_id, case_version_id, tags, body,
                              moderation_state, created_at, updated_at
                    """
                ),
                {
                    "id": reason.id,
                    "actor_id": reason.actor_id,
                    "session_id": reason.session_id,
                    "case_version_id": reason.case_version_id,
                    "tags": json.dumps(list(reason.tags), separators=(",", ":")),
                    "body": reason.body,
                    "moderation_state": reason.moderation_state.value,
                    "created_at": reason.created_at,
                    "updated_at": reason.updated_at,
                },
            ).mappings().one()
        return self._reason(row)

    def get(self, reason_id: UUID) -> CommunityReason | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, actor_id, session_id, case_version_id, tags, body,
                           moderation_state, created_at, updated_at
                    FROM community.reason WHERE id = :id
                    """
                ),
                {"id": reason_id},
            ).mappings().one_or_none()
        return None if row is None else self._reason(row)

    def public_snapshot(self, case_version_id: UUID, *, limit: int) -> CommunityReasonSnapshot:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT id, tags, body, created_at
                    FROM community.reason
                    WHERE case_version_id = :case_version_id
                      AND moderation_state IN ('NOT_REQUIRED','ALLOWED')
                    ORDER BY created_at DESC, id DESC
                    LIMIT :limit
                    """
                ),
                {"case_version_id": case_version_id, "limit": limit},
            ).mappings().all()
            total = connection.execute(
                text(
                    """
                    SELECT count(*)
                    FROM community.reason
                    WHERE case_version_id = :case_version_id
                      AND moderation_state IN ('NOT_REQUIRED','ALLOWED')
                    """
                ),
                {"case_version_id": case_version_id},
            ).scalar_one()
            reaction_rows = connection.execute(
                text(
                    """
                    SELECT rr.reason_id, rr.reaction_code, count(*) AS count
                    FROM community.reason_reaction rr
                    JOIN community.reason r ON r.id = rr.reason_id
                    WHERE r.case_version_id = :case_version_id
                      AND r.moderation_state IN ('NOT_REQUIRED','ALLOWED')
                    GROUP BY rr.reason_id, rr.reaction_code
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().all()

        reactions: dict[UUID, dict[str, int]] = {}
        for row in reaction_rows:
            reactions.setdefault(row["reason_id"], {})[row["reaction_code"]] = int(row["count"])
        tag_counts: Counter[str] = Counter()
        items: list[PublicCommunityReason] = []
        for row in rows:
            tags = tuple(row["tags"])
            tag_counts.update(set(tags))
            items.append(
                PublicCommunityReason(
                    id=row["id"],
                    tags=tags,
                    body=row["body"],
                    reaction_counts=MappingProxyType(dict(reactions.get(row["id"], {}))),
                    created_at=row["created_at"],
                )
            )
        return CommunityReasonSnapshot(
            reasons=tuple(items),
            tag_pattern_counts=MappingProxyType(dict(tag_counts)),
            sample_size=int(total),
        )

    def set_reaction(
        self,
        *,
        reason_id: UUID,
        actor_id: UUID,
        reaction: ReasonReaction,
        created_at: datetime,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO community.reason_reaction (
                        reason_id, actor_id, reaction_code, created_at
                    ) VALUES (:reason_id, :actor_id, :reaction_code, :created_at)
                    ON CONFLICT (reason_id, actor_id) DO UPDATE SET
                        reaction_code = EXCLUDED.reaction_code,
                        created_at = EXCLUDED.created_at
                    """
                ),
                {
                    "reason_id": reason_id,
                    "actor_id": actor_id,
                    "reaction_code": reaction.value,
                    "created_at": created_at,
                },
            )

    def report(
        self,
        *,
        report_id: UUID,
        reason_id: UUID,
        reporter_actor_id: UUID,
        report_code: ReasonReportCode,
        created_at: datetime,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO community.reason_report (
                        id, reason_id, reporter_actor_id, report_code, created_at
                    ) VALUES (:id, :reason_id, :reporter_actor_id, :report_code, :created_at)
                    ON CONFLICT (reason_id, reporter_actor_id, report_code) DO NOTHING
                    """
                ),
                {
                    "id": report_id,
                    "reason_id": reason_id,
                    "reporter_actor_id": reporter_actor_id,
                    "report_code": report_code.value,
                    "created_at": created_at,
                },
            )

    def moderate(
        self,
        *,
        reason_id: UUID,
        state: CommunityReasonModeration,
        updated_at: datetime,
    ) -> CommunityReason | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE community.reason
                    SET moderation_state = :state, updated_at = :updated_at
                    WHERE id = :reason_id
                    RETURNING id, actor_id, session_id, case_version_id, tags, body,
                              moderation_state, created_at, updated_at
                    """
                ),
                {"reason_id": reason_id, "state": state.value, "updated_at": updated_at},
            ).mappings().one_or_none()
        return None if row is None else self._reason(row)

    @staticmethod
    def _reason(row) -> CommunityReason:
        return CommunityReason(
            id=row["id"],
            actor_id=row["actor_id"],
            session_id=row["session_id"],
            case_version_id=row["case_version_id"],
            tags=tuple(row["tags"]),
            body=row["body"],
            moderation_state=CommunityReasonModeration(row["moderation_state"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
