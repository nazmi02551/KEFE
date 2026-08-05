from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.community_reason.models import (
    CommunityReason,
    CommunityReasonModeration,
    CommunityReasonModerationAudit,
    CommunityReasonModerationItem,
    CommunityReasonModerationQueueKind,
    CommunityReasonModerationWriteResult,
    CommunityReasonSnapshot,
    ReasonReaction,
    ReasonReportCode,
)


class CommunityReasonRepository(Protocol):
    def create_or_replace(self, reason: CommunityReason) -> CommunityReason: ...

    def get(self, reason_id: UUID) -> CommunityReason | None: ...

    def public_snapshot(self, case_version_id: UUID, *, limit: int) -> CommunityReasonSnapshot: ...

    def set_reaction(
        self,
        *,
        reason_id: UUID,
        actor_id: UUID,
        reaction: ReasonReaction,
        created_at: datetime,
    ) -> None: ...

    def report(
        self,
        *,
        report_id: UUID,
        reason_id: UUID,
        reporter_actor_id: UUID,
        report_code: ReasonReportCode,
        created_at: datetime,
    ) -> None: ...

    def moderation_queue(
        self,
        *,
        kind: CommunityReasonModerationQueueKind,
        limit: int,
        offset: int,
        case_version_id: UUID | None,
        report_code: ReasonReportCode | None,
    ) -> tuple[CommunityReasonModerationItem, ...]: ...

    def moderation_inspection(
        self,
        reason_id: UUID,
    ) -> CommunityReasonModerationItem | None: ...

    def moderation_audit(
        self,
        *,
        reason_id: UUID,
        limit: int,
    ) -> tuple[CommunityReasonModerationAudit, ...]: ...

    def moderate(
        self,
        *,
        audit_id: UUID,
        reason_id: UUID,
        state: CommunityReasonModeration,
        actor_ref: str,
        rationale: str,
        updated_at: datetime,
    ) -> CommunityReasonModerationWriteResult: ...
