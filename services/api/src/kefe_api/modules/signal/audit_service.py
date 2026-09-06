from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from kefe_api.modules.signal.audit_models import (
    SignalAuditEvent,
    SignalAuditEventType,
)


class SignalAuditService:
    def __init__(self) -> None:
        self._audit_chains_by_signal: dict[UUID, list[SignalAuditEvent]] = {}

    def append_audit_event(
        self,
        *,
        signal_id: UUID,
        case_version_id: UUID,
        event_type: SignalAuditEventType,
        actor_ref: str,
        evidence_snapshot: dict[str, Any],
        occurred_at: datetime | None = None,
    ) -> SignalAuditEvent:
        chain = self._audit_chains_by_signal.setdefault(signal_id, [])
        previous_hash = chain[-1].entry_hash if chain else None
        event_time = occurred_at or datetime.now(UTC)
        audit_id = uuid4()

        payload_bytes = json.dumps(
            {
                "audit_id": str(audit_id),
                "signal_id": str(signal_id),
                "case_version_id": str(case_version_id),
                "event_type": event_type.value,
                "actor_ref": actor_ref,
                "evidence_snapshot": evidence_snapshot,
                "occurred_at": event_time.isoformat(),
                "previous_hash": previous_hash,
            },
            sort_keys=True,
        ).encode("utf-8")

        entry_hash = hashlib.sha256(payload_bytes).hexdigest()

        event = SignalAuditEvent(
            audit_id=audit_id,
            signal_id=signal_id,
            case_version_id=case_version_id,
            event_type=event_type,
            actor_ref=actor_ref,
            evidence_snapshot=evidence_snapshot,
            occurred_at=event_time,
            previous_hash=previous_hash,
            entry_hash=entry_hash,
        )

        chain.append(event)
        return event

    def get_audit_trail(self, signal_id: UUID) -> list[SignalAuditEvent]:
        return list(self._audit_chains_by_signal.get(signal_id, []))

    def verify_chain_integrity(self, signal_id: UUID) -> bool:
        chain = self._audit_chains_by_signal.get(signal_id, [])
        previous_hash = None

        for event in chain:
            if event.previous_hash != previous_hash:
                return False

            payload_bytes = json.dumps(
                {
                    "audit_id": str(event.audit_id),
                    "signal_id": str(event.signal_id),
                    "case_version_id": str(event.case_version_id),
                    "event_type": event.event_type.value,
                    "actor_ref": event.actor_ref,
                    "evidence_snapshot": event.evidence_snapshot,
                    "occurred_at": event.occurred_at.isoformat(),
                    "previous_hash": previous_hash,
                },
                sort_keys=True,
            ).encode("utf-8")

            expected_hash = hashlib.sha256(payload_bytes).hexdigest()
            if event.entry_hash != expected_hash:
                return False

            previous_hash = event.entry_hash

        return True
