from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.modules.sharing.models import ShareRecord


class InMemoryShareRepository:
    def __init__(self) -> None:
        self._records: dict[UUID, ShareRecord] = {}
        self._by_token: dict[str, UUID] = {}

    def create(self, record: ShareRecord) -> None:
        self._records[record.id] = record
        self._by_token[record.token_hash] = record.id

    def get_by_token_hash(self, token_hash: str) -> ShareRecord | None:
        share_id = self._by_token.get(token_hash)
        return None if share_id is None else self._records.get(share_id)

    def revoke(self, *, share_id: UUID, actor_id: UUID, revoked_at: datetime) -> bool:
        record = self._records.get(share_id)
        if record is None or record.actor_id != actor_id:
            return False
        if record.revoked_at is not None:
            return True
        self._records[share_id] = ShareRecord(
            id=record.id,
            token_hash=record.token_hash,
            actor_id=record.actor_id,
            session_id=record.session_id,
            case_id=record.case_id,
            case_version_id=record.case_version_id,
            include_decision=record.include_decision,
            decision_snapshot=record.decision_snapshot,
            created_at=record.created_at,
            expires_at=record.expires_at,
            revoked_at=revoked_at,
        )
        return True
