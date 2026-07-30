from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from kefe_api.modules.decision.in_memory import InMemoryDecisionRepository
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository
from kefe_api.modules.privacy.models import PrivacyDeletionReceipt


class InMemoryPrivacyRepository:
    def __init__(
        self,
        *,
        decision_repository: InMemoryDecisionRepository,
        identity_repository: InMemoryIdentityRepository,
    ) -> None:
        self._decision = decision_repository
        self._identity = identity_repository

    def export_actor_data(self, actor_id: UUID) -> dict[str, object]:
        sessions = [
            {
                "session_id": str(session.id),
                "case_id": str(session.case_id),
                "case_version_id": str(session.case_version_id),
                "state": session.state.value,
                "started_at": session.started_at.isoformat(),
                "committed_at": (
                    session.committed_at.isoformat() if session.committed_at else None
                ),
                "responses": {
                    str(key): value for key, value in session.responses.items()
                },
            }
            for session in self._decision._sessions.values()
            if session.actor_id == actor_id
        ]
        private_reasons = [
            {
                "session_id": str(reason.session_id),
                "tags": list(reason.tags),
                "text": reason.text,
                "moderation_state": reason.moderation_state.value,
            }
            for session_id, reason in self._decision._reasons.items()
            if self._decision._sessions.get(session_id) is not None
            and self._decision._sessions[session_id].actor_id == actor_id
        ]
        return {
            "weigh_sessions": sessions,
            "private_reasons": private_reasons,
        }

    def delete_actor_data(
        self,
        *,
        actor_id: UUID,
        actor_kind: str,
        deleted_at: datetime,
    ) -> PrivacyDeletionReceipt:
        session_ids = {
            session.id
            for session in self._decision._sessions.values()
            if session.actor_id == actor_id
        }
        for session_id in session_ids:
            self._decision._sessions.pop(session_id, None)
            self._decision._reasons.pop(session_id, None)
            self._decision._revisions.pop(session_id, None)
            self._decision._revision_drafts = {
                key: value
                for key, value in self._decision._revision_drafts.items()
                if key[0] != session_id
            }
            self._decision._exposures.pop(session_id, None)
            self._decision._interventions.pop(session_id, None)
            self._decision._deltas.pop(session_id, None)
        for event in self._decision.events:
            if event.get("aggregate_id") in session_ids:
                payload = event.get("payload")
                if isinstance(payload, dict):
                    payload.pop("actor_id", None)
                    payload["actor_deleted"] = True
        self._identity.delete_actor(actor_id, now=deleted_at)
        return PrivacyDeletionReceipt(
            receipt_id=uuid4(),
            actor_id=actor_id,
            actor_kind=actor_kind,
            deleted_at=deleted_at,
            private_data_deleted=True,
            aggregate_contributions_anonymized=True,
            policy_version="MVP_PRIVACY_V1",
        )
