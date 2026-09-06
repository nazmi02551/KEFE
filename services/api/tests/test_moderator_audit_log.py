from __future__ import annotations

from datetime import datetime, timezone

from kefe_api.modules.decision.moderator_audit_log import (
    ModerationActionType,
    ModeratorAuditLogResult,
    ModeratorAuditLogService,
)


def test_moderator_audit_log_records_correctly() -> None:
    ts = datetime(2026, 9, 1, 15, 0, 0, tzinfo=timezone.utc)

    r = ModeratorAuditLogService.record_action(
        audit_id="aud_001",
        target_resource_id="rsn_9814",
        moderator_id="mod_412",
        action_type=ModerationActionType.REASON_REMOVED_POLICY_BREACH,
        policy_rule_reference="KEFE-TOS-SEC-4.2",
        justification_text="Kişisel verilerin ifşası ve tehdit içeren ifadeler tespit edildiği için gerekçe kaldırılmıştır.",
        timestamp=ts,
    )

    assert isinstance(r, ModeratorAuditLogResult)
    assert r.action_type == ModerationActionType.REASON_REMOVED_POLICY_BREACH
    assert len(r.action_hash) == 64


def test_moderator_audit_log_invalid_justification() -> None:
    failed = False
    try:
        ModeratorAuditLogService.record_action(
            audit_id="aud_002",
            target_resource_id="rsn_9814",
            moderator_id="mod_1",
            action_type=ModerationActionType.FLAG_DISMISSED_VALID,
            policy_rule_reference="REF",
            justification_text="Kısa",  # < 10
        )
    except ValueError:
        failed = True

    assert failed is True
