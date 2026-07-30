from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.sharing.models import ShareRecord


class PostgresShareRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create(self, record: ShareRecord) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO sharing.share_record (
                        id, token_hash, actor_id, session_id, case_id, case_version_id,
                        include_decision, decision_snapshot, created_at, expires_at, revoked_at
                    ) VALUES (
                        :id, :token_hash, :actor_id, :session_id, :case_id, :case_version_id,
                        :include_decision, CAST(:decision_snapshot AS jsonb),
                        :created_at, :expires_at, :revoked_at
                    )
                    """
                ),
                {
                    "id": record.id,
                    "token_hash": record.token_hash,
                    "actor_id": record.actor_id,
                    "session_id": record.session_id,
                    "case_id": record.case_id,
                    "case_version_id": record.case_version_id,
                    "include_decision": record.include_decision,
                    "decision_snapshot": (
                        json.dumps(record.decision_snapshot, separators=(",", ":"))
                        if record.decision_snapshot is not None
                        else None
                    ),
                    "created_at": record.created_at,
                    "expires_at": record.expires_at,
                    "revoked_at": record.revoked_at,
                },
            )

    def get_by_token_hash(self, token_hash: str) -> ShareRecord | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, token_hash, actor_id, session_id, case_id, case_version_id,
                           include_decision, decision_snapshot, created_at, expires_at, revoked_at
                    FROM sharing.share_record
                    WHERE token_hash = :token_hash
                    """
                ),
                {"token_hash": token_hash},
            ).mappings().one_or_none()
        return None if row is None else self._record(row)

    def revoke(self, *, share_id: UUID, actor_id: UUID, revoked_at: datetime) -> bool:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE sharing.share_record
                    SET revoked_at = COALESCE(revoked_at, :revoked_at)
                    WHERE id = :share_id AND actor_id = :actor_id
                    RETURNING id
                    """
                ),
                {"share_id": share_id, "actor_id": actor_id, "revoked_at": revoked_at},
            ).scalar_one_or_none()
        return row is not None

    @staticmethod
    def _record(row) -> ShareRecord:
        return ShareRecord(
            id=row["id"],
            token_hash=row["token_hash"],
            actor_id=row["actor_id"],
            session_id=row["session_id"],
            case_id=row["case_id"],
            case_version_id=row["case_version_id"],
            include_decision=row["include_decision"],
            decision_snapshot=(
                dict(row["decision_snapshot"]) if row["decision_snapshot"] is not None else None
            ),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
        )
