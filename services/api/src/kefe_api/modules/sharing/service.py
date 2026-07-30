from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.decision.models import WeighState
from kefe_api.modules.decision.ports import DecisionRepository
from kefe_api.modules.sharing.models import PublicShare, ShareRecord
from kefe_api.modules.sharing.ports import ShareRepository


class ShareService:
    def __init__(
        self,
        *,
        repository: ShareRepository,
        decision_repository: DecisionRepository,
        ttl_days: int = 30,
    ) -> None:
        self._repo = repository
        self._decision = decision_repository
        self._ttl = timedelta(days=ttl_days)

    def create(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        include_decision: bool,
    ) -> tuple[ShareRecord, str]:
        session = self._decision.get_session(session_id)
        if session is None or session.actor_id != actor_id:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        if session.state is not WeighState.COMMITTED:
            raise DomainError("SHARE_COMMIT_REQUIRED", "Commit is required before sharing", 403)
        case = self._decision.get_case_version(session.case_version_id)
        if case is None:
            raise DomainError("CASE_VERSION_STALE", "Case version is no longer available", 409)

        decision_snapshot = None
        if include_decision:
            for question in case.questions:
                if question.response_type != "SINGLE_CHOICE":
                    continue
                if question.id not in session.responses:
                    continue
                decision_snapshot = {
                    "question_id": str(question.id),
                    "value": session.responses[question.id],
                }
                break

        now = datetime.now(UTC)
        token = f"kefe_s_{secrets.token_urlsafe(24)}"
        record = ShareRecord(
            id=uuid4(),
            token_hash=self._hash(token),
            actor_id=actor_id,
            session_id=session.id,
            case_id=session.case_id,
            case_version_id=session.case_version_id,
            include_decision=include_decision,
            decision_snapshot=decision_snapshot,
            created_at=now,
            expires_at=now + self._ttl,
        )
        self._repo.create(record)
        self._decision.append_event(
            "share.created",
            session.id,
            {
                "share_id": str(record.id),
                "case_version_id": str(record.case_version_id),
                "include_decision": include_decision,
            },
        )
        return record, token

    def read_public(self, token: str) -> PublicShare:
        record = self._repo.get_by_token_hash(self._hash(token.strip()))
        now = datetime.now(UTC)
        if record is None or record.revoked_at is not None or record.expires_at <= now:
            raise DomainError("SHARE_NOT_FOUND", "Share not found", 404)
        case = self._decision.get_case_version(record.case_version_id)
        if case is None:
            raise DomainError("SHARE_NOT_FOUND", "Share not found", 404)
        return PublicShare(
            share_id=record.id,
            case_id=record.case_id,
            case_version_id=record.case_version_id,
            title=case.title,
            summary=case.summary,
            primary_domain=case.primary_domain,
            decision=record.decision_snapshot if record.include_decision else None,
            created_at=record.created_at,
            expires_at=record.expires_at,
        )

    def revoke(self, *, actor_id: UUID, share_id: UUID) -> None:
        if not self._repo.revoke(
            share_id=share_id,
            actor_id=actor_id,
            revoked_at=datetime.now(UTC),
        ):
            raise DomainError("SHARE_NOT_FOUND", "Share not found", 404)

    @staticmethod
    def _hash(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()
