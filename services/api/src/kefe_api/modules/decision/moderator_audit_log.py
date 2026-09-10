from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum


class ModerationActionType(StrEnum):
    REASON_REMOVED_POLICY_BREACH = "REASON_REMOVED_POLICY_BREACH"
    FLAG_DISMISSED_VALID = "FLAG_DISMISSED_VALID"
    CASE_VERSION_FREEZE = "CASE_VERSION_FREEZE"
    USER_WARNING_ISSUED = "USER_WARNING_ISSUED"


@dataclass(frozen=True, slots=True)
class ModeratorAuditLogResult:
    audit_id: str
    target_resource_id: str
    moderator_id: str
    action_type: ModerationActionType
    policy_rule_reference: str
    justification_text: str
    action_hash: str
    created_at_utc: str


class ModeratorAuditLogService:
    @staticmethod
    def record_action(
        *,
        audit_id: str,
        target_resource_id: str,
        moderator_id: str,
        action_type: ModerationActionType,
        policy_rule_reference: str,
        justification_text: str,
        timestamp: datetime | None = None,
    ) -> ModeratorAuditLogResult:
        if len(moderator_id.strip()) < 3:
            raise ValueError("moderator_id must have at least 3 characters")
        if len(policy_rule_reference.strip()) < 3:
            raise ValueError("policy_rule_reference must have at least 3 characters")
        if len(justification_text.strip()) < 10:
            raise ValueError("justification_text must have at least 10 characters")

        ts = timestamp or datetime.now(UTC)
        ts_str = ts.isoformat()

        raw_payload = f"{audit_id}:{target_resource_id}:{moderator_id}:{action_type}:{policy_rule_reference}:{justification_text}:{ts_str}"
        action_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

        return ModeratorAuditLogResult(
            audit_id=audit_id.strip(),
            target_resource_id=target_resource_id.strip(),
            moderator_id=moderator_id.strip(),
            action_type=action_type,
            policy_rule_reference=policy_rule_reference.strip(),
            justification_text=justification_text.strip(),
            action_hash=action_hash,
            created_at_utc=ts_str,
        )
