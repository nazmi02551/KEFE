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
    CommunityReasonModerationAudit,
    CommunityReasonModerationDecision,
    CommunityReasonModerationItem,
    CommunityReasonModerationQueueKind,
    CommunityReasonModerationWriteResult,
    CommunityReasonModerationWriteStatus,
    CommunityReasonSnapshot,
    PublicCommunityReason,
    ReasonReaction,
    ReasonReportCode,
)


_MODERATION_SELECT = """
    SELECT
        r.id AS reason_id,
        r.case_version_id,
        r.tags,
        r.body,
        r.moderation_state,
        r.created_at,
        r.updated_at,
        COALESCE(rs.report_count, 0) AS report_count,
        COALESCE(rc.report_counts_by_code, '{}'::jsonb) AS report_counts_by_code,
        rs.latest_reported_at,
        CASE
            WHEN :kind = 'PENDING' THEN r.created_at
            ELSE rs.latest_reported_at
        END AS candidate_at
    FROM community.reason r
    LEFT JOIN LATERAL (
        SELECT count(*) AS report_count, max(created_at) AS latest_reported_at
        FROM community.reason_report
        WHERE reason_id = r.id
    ) rs ON TRUE
    LEFT JOIN LATERAL (
        SELECT jsonb_object_agg(report_code, code_count) AS report_counts_by_code
        FROM (
            SELECT report_code, count(*) AS code_count
            FROM community.reason_report
            WHERE reason_id = r.id
            GROUP BY report_code
        ) grouped_reports
    ) rc ON TRUE
    LEFT JOIN LATERAL (
        SELECT max(created_at) AS latest_audit_at
        FROM community.reason_moderation_audit
        WHERE reason_id = r.id
    ) la ON TRUE
"""


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

    def moderation_queue(
        self,
        *,
        kind: CommunityReasonModerationQueueKind,
        limit: int,
        offset: int,
        case_version_id: UUID | None,
        report_code: ReasonReportCode | None,
    ) -> tuple[CommunityReasonModerationItem, ...]:
        query = (
            _MODERATION_SELECT
            + """
            WHERE (
                (:kind = 'PENDING' AND r.moderation_state = 'PENDING')
                OR (
                    :kind = 'REPORTED'
                    AND r.moderation_state IN ('NOT_REQUIRED', 'ALLOWED')
                    AND rs.latest_reported_at IS NOT NULL
                    AND (
                        la.latest_audit_at IS NULL
                        OR rs.latest_reported_at > la.latest_audit_at
                    )
                )
            )
              AND (:case_version_id IS NULL OR r.case_version_id = :case_version_id)
              AND (
                :report_code IS NULL
                OR EXISTS (
                    SELECT 1
                    FROM community.reason_report filtered_report
                    WHERE filtered_report.reason_id = r.id
                      AND filtered_report.report_code = :report_code
                )
              )
            ORDER BY candidate_at ASC, r.id ASC
            LIMIT :limit OFFSET :offset
            """
        )
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(query),
                {
                    "kind": kind.value,
                    "case_version_id": case_version_id,
                    "report_code": report_code.value if report_code is not None else None,
                    "limit": limit,
                    "offset": offset,
                },
            ).mappings().all()
        return tuple(self._moderation_item(row) for row in rows)

    def moderation_inspection(
        self,
        reason_id: UUID,
    ) -> CommunityReasonModerationItem | None:
        query = _MODERATION_SELECT + " WHERE r.id = :reason_id"
        with self._engine.connect() as connection:
            row = connection.execute(
                text(query),
                {"kind": "REPORTED", "reason_id": reason_id},
            ).mappings().one_or_none()
        return None if row is None else self._moderation_item(row)

    def moderation_audit(
        self,
        *,
        reason_id: UUID,
        limit: int,
    ) -> tuple[CommunityReasonModerationAudit, ...]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT id, reason_id, actor_ref, previous_state, decided_state,
                           rationale, created_at
                    FROM community.reason_moderation_audit
                    WHERE reason_id = :reason_id
                    ORDER BY created_at DESC, id DESC
                    LIMIT :limit
                    """
                ),
                {"reason_id": reason_id, "limit": limit},
            ).mappings().all()
        return tuple(self._audit(row) for row in rows)

    def moderate(
        self,
        *,
        audit_id: UUID,
        reason_id: UUID,
        state: CommunityReasonModeration,
        actor_ref: str,
        rationale: str,
        updated_at: datetime,
    ) -> CommunityReasonModerationWriteResult:
        with self._engine.begin() as connection:
            current = connection.execute(
                text(
                    """
                    SELECT id, actor_id, session_id, case_version_id, tags, body,
                           moderation_state, created_at, updated_at
                    FROM community.reason
                    WHERE id = :reason_id
                    FOR UPDATE
                    """
                ),
                {"reason_id": reason_id},
            ).mappings().one_or_none()
            if current is None:
                return CommunityReasonModerationWriteResult(
                    status=CommunityReasonModerationWriteStatus.NOT_FOUND
                )
            previous_state = CommunityReasonModeration(current["moderation_state"])
            if not self._decision_allowed(connection, reason_id, previous_state):
                return CommunityReasonModerationWriteResult(
                    status=CommunityReasonModerationWriteStatus.CONFLICT,
                    current_state=previous_state,
                )
            updated_row = connection.execute(
                text(
                    """
                    UPDATE community.reason
                    SET moderation_state = :state, updated_at = :updated_at
                    WHERE id = :reason_id
                    RETURNING id, actor_id, session_id, case_version_id, tags, body,
                              moderation_state, created_at, updated_at
                    """
                ),
                {
                    "reason_id": reason_id,
                    "state": state.value,
                    "updated_at": updated_at,
                },
            ).mappings().one()
            audit_row = connection.execute(
                text(
                    """
                    INSERT INTO community.reason_moderation_audit (
                        id, reason_id, actor_ref, previous_state, decided_state,
                        rationale, created_at
                    ) VALUES (
                        :id, :reason_id, :actor_ref, :previous_state, :decided_state,
                        :rationale, :created_at
                    )
                    RETURNING id, reason_id, actor_ref, previous_state, decided_state,
                              rationale, created_at
                    """
                ),
                {
                    "id": audit_id,
                    "reason_id": reason_id,
                    "actor_ref": actor_ref,
                    "previous_state": previous_state.value,
                    "decided_state": state.value,
                    "rationale": rationale,
                    "created_at": updated_at,
                },
            ).mappings().one()
        reason = self._reason(updated_row)
        audit = self._audit(audit_row)
        return CommunityReasonModerationWriteResult(
            status=CommunityReasonModerationWriteStatus.APPLIED,
            decision=CommunityReasonModerationDecision(reason=reason, audit=audit),
            current_state=reason.moderation_state,
        )

    @staticmethod
    def _decision_allowed(connection, reason_id: UUID, state: CommunityReasonModeration) -> bool:
        if state is CommunityReasonModeration.PENDING:
            return True
        if state not in {
            CommunityReasonModeration.NOT_REQUIRED,
            CommunityReasonModeration.ALLOWED,
        }:
            return False
        timestamps = connection.execute(
            text(
                """
                SELECT
                    (SELECT max(created_at) FROM community.reason_report
                     WHERE reason_id = :reason_id) AS latest_reported_at,
                    (SELECT max(created_at) FROM community.reason_moderation_audit
                     WHERE reason_id = :reason_id) AS latest_audit_at
                """
            ),
            {"reason_id": reason_id},
        ).mappings().one()
        latest_reported_at = timestamps["latest_reported_at"]
        latest_audit_at = timestamps["latest_audit_at"]
        return latest_reported_at is not None and (
            latest_audit_at is None or latest_reported_at > latest_audit_at
        )

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

    @staticmethod
    def _moderation_item(row) -> CommunityReasonModerationItem:
        return CommunityReasonModerationItem(
            reason_id=row["reason_id"],
            case_version_id=row["case_version_id"],
            tags=tuple(row["tags"]),
            body=row["body"],
            moderation_state=CommunityReasonModeration(row["moderation_state"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            report_count=int(row["report_count"]),
            report_counts_by_code=MappingProxyType(
                {str(key): int(value) for key, value in dict(row["report_counts_by_code"]).items()}
            ),
            latest_reported_at=row["latest_reported_at"],
            candidate_at=row["candidate_at"],
        )

    @staticmethod
    def _audit(row) -> CommunityReasonModerationAudit:
        return CommunityReasonModerationAudit(
            audit_id=row["id"],
            reason_id=row["reason_id"],
            actor_ref=row["actor_ref"],
            previous_state=CommunityReasonModeration(row["previous_state"]),
            decided_state=CommunityReasonModeration(row["decided_state"]),
            rationale=row["rationale"],
            created_at=row["created_at"],
        )
