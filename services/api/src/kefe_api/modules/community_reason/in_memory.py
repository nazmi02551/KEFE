from __future__ import annotations

from collections import Counter
from datetime import datetime
from types import MappingProxyType
from uuid import UUID

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


class InMemoryCommunityReasonRepository:
    def __init__(self) -> None:
        self._reasons: dict[UUID, CommunityReason] = {}
        self._by_actor_session: dict[tuple[UUID, UUID], UUID] = {}
        self._reactions: dict[tuple[UUID, UUID], ReasonReaction] = {}
        self._reports: dict[
            tuple[UUID, UUID, ReasonReportCode],
            tuple[UUID, datetime],
        ] = {}
        self._audits: list[CommunityReasonModerationAudit] = []

    def create_or_replace(self, reason: CommunityReason) -> CommunityReason:
        key = (reason.actor_id, reason.session_id)
        existing_id = self._by_actor_session.get(key)
        if existing_id is not None:
            previous = self._reasons[existing_id]
            reason = CommunityReason(
                id=previous.id,
                actor_id=previous.actor_id,
                session_id=previous.session_id,
                case_version_id=previous.case_version_id,
                tags=reason.tags,
                body=reason.body,
                moderation_state=reason.moderation_state,
                created_at=previous.created_at,
                updated_at=reason.updated_at,
            )
        self._reasons[reason.id] = reason
        self._by_actor_session[key] = reason.id
        return reason

    def get(self, reason_id: UUID) -> CommunityReason | None:
        return self._reasons.get(reason_id)

    def public_snapshot(self, case_version_id: UUID, *, limit: int) -> CommunityReasonSnapshot:
        public = [
            reason
            for reason in self._reasons.values()
            if reason.case_version_id == case_version_id and reason.publicly_readable
        ]
        public.sort(key=lambda item: (item.created_at, str(item.id)), reverse=True)
        tag_counts = Counter(
            tag
            for reason in public
            for tag in set(reason.tags)
        )
        rendered: list[PublicCommunityReason] = []
        for reason in public[:limit]:
            reactions = Counter(
                reaction.value
                for (reason_id, _), reaction in self._reactions.items()
                if reason_id == reason.id
            )
            rendered.append(
                PublicCommunityReason(
                    id=reason.id,
                    tags=reason.tags,
                    body=reason.body,
                    reaction_counts=MappingProxyType(dict(reactions)),
                    created_at=reason.created_at,
                )
            )
        return CommunityReasonSnapshot(
            reasons=tuple(rendered),
            tag_pattern_counts=MappingProxyType(dict(tag_counts)),
            sample_size=len(public),
        )

    def set_reaction(
        self,
        *,
        reason_id: UUID,
        actor_id: UUID,
        reaction: ReasonReaction,
        created_at: datetime,
    ) -> None:
        del created_at
        self._reactions[(reason_id, actor_id)] = reaction

    def report(
        self,
        *,
        report_id: UUID,
        reason_id: UUID,
        reporter_actor_id: UUID,
        report_code: ReasonReportCode,
        created_at: datetime,
    ) -> None:
        key = (reason_id, reporter_actor_id, report_code)
        self._reports.setdefault(key, (report_id, created_at))

    def moderation_queue(
        self,
        *,
        kind: CommunityReasonModerationQueueKind,
        limit: int,
        offset: int,
        case_version_id: UUID | None,
        report_code: ReasonReportCode | None,
    ) -> tuple[CommunityReasonModerationItem, ...]:
        items: list[CommunityReasonModerationItem] = []
        for reason in self._reasons.values():
            if case_version_id is not None and reason.case_version_id != case_version_id:
                continue
            report_counts, latest_reported_at = self._report_summary(reason.id)
            if report_code is not None and report_counts.get(report_code.value, 0) == 0:
                continue
            latest_audit_at = self._latest_audit_at(reason.id)
            if kind is CommunityReasonModerationQueueKind.PENDING:
                if reason.moderation_state is not CommunityReasonModeration.PENDING:
                    continue
                candidate_at = reason.created_at
            else:
                if reason.moderation_state not in {
                    CommunityReasonModeration.NOT_REQUIRED,
                    CommunityReasonModeration.ALLOWED,
                }:
                    continue
                if latest_reported_at is None:
                    continue
                if latest_audit_at is not None and latest_reported_at <= latest_audit_at:
                    continue
                candidate_at = latest_reported_at
            items.append(
                self._moderation_item(
                    reason,
                    report_counts=report_counts,
                    latest_reported_at=latest_reported_at,
                    candidate_at=candidate_at,
                )
            )
        items.sort(key=lambda item: (item.candidate_at, str(item.reason_id)))
        return tuple(items[offset : offset + limit])

    def count_moderation_queue(
        self,
        *,
        kind: CommunityReasonModerationQueueKind,
        case_version_id: UUID | None = None,
        report_code: ReasonReportCode | None = None,
    ) -> int:
        return len(
            self.moderation_queue(
                kind=kind,
                limit=max(len(self._reasons), 1),
                offset=0,
                case_version_id=case_version_id,
                report_code=report_code,
            )
        )

    def moderation_inspection(
        self,
        reason_id: UUID,
    ) -> CommunityReasonModerationItem | None:
        reason = self._reasons.get(reason_id)
        if reason is None:
            return None
        report_counts, latest_reported_at = self._report_summary(reason_id)
        return self._moderation_item(
            reason,
            report_counts=report_counts,
            latest_reported_at=latest_reported_at,
            candidate_at=latest_reported_at or reason.created_at,
        )

    def moderation_audit(
        self,
        *,
        reason_id: UUID,
        limit: int,
    ) -> tuple[CommunityReasonModerationAudit, ...]:
        audits = [audit for audit in self._audits if audit.reason_id == reason_id]
        audits.sort(key=lambda audit: (audit.created_at, str(audit.audit_id)), reverse=True)
        return tuple(audits[:limit])

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
        reason = self._reasons.get(reason_id)
        if reason is None:
            return CommunityReasonModerationWriteResult(
                status=CommunityReasonModerationWriteStatus.NOT_FOUND
            )
        if not self._decision_allowed(reason):
            return CommunityReasonModerationWriteResult(
                status=CommunityReasonModerationWriteStatus.CONFLICT,
                current_state=reason.moderation_state,
            )
        updated = CommunityReason(
            id=reason.id,
            actor_id=reason.actor_id,
            session_id=reason.session_id,
            case_version_id=reason.case_version_id,
            tags=reason.tags,
            body=reason.body,
            moderation_state=state,
            created_at=reason.created_at,
            updated_at=updated_at,
        )
        audit = CommunityReasonModerationAudit(
            audit_id=audit_id,
            reason_id=reason.id,
            actor_ref=actor_ref,
            previous_state=reason.moderation_state,
            decided_state=state,
            rationale=rationale,
            created_at=updated_at,
        )
        self._reasons[reason_id] = updated
        self._audits.append(audit)
        return CommunityReasonModerationWriteResult(
            status=CommunityReasonModerationWriteStatus.APPLIED,
            decision=CommunityReasonModerationDecision(reason=updated, audit=audit),
            current_state=updated.moderation_state,
        )

    def _decision_allowed(self, reason: CommunityReason) -> bool:
        if reason.moderation_state is CommunityReasonModeration.PENDING:
            return True
        if reason.moderation_state not in {
            CommunityReasonModeration.NOT_REQUIRED,
            CommunityReasonModeration.ALLOWED,
        }:
            return False
        _, latest_reported_at = self._report_summary(reason.id)
        if latest_reported_at is None:
            return False
        latest_audit_at = self._latest_audit_at(reason.id)
        return latest_audit_at is None or latest_reported_at > latest_audit_at

    def _report_summary(self, reason_id: UUID) -> tuple[Counter[str], datetime | None]:
        reports = [
            (report_code, created_at)
            for (stored_reason_id, _, report_code), (_, created_at) in self._reports.items()
            if stored_reason_id == reason_id
        ]
        counts: Counter[str] = Counter(report_code.value for report_code, _ in reports)
        latest = max((created_at for _, created_at in reports), default=None)
        return counts, latest

    def _latest_audit_at(self, reason_id: UUID) -> datetime | None:
        return max(
            (audit.created_at for audit in self._audits if audit.reason_id == reason_id),
            default=None,
        )

    @staticmethod
    def _moderation_item(
        reason: CommunityReason,
        *,
        report_counts: Counter[str],
        latest_reported_at: datetime | None,
        candidate_at: datetime,
    ) -> CommunityReasonModerationItem:
        return CommunityReasonModerationItem(
            reason_id=reason.id,
            case_version_id=reason.case_version_id,
            tags=reason.tags,
            body=reason.body,
            moderation_state=reason.moderation_state,
            created_at=reason.created_at,
            updated_at=reason.updated_at,
            report_count=sum(report_counts.values()),
            report_counts_by_code=MappingProxyType(dict(report_counts)),
            latest_reported_at=latest_reported_at,
            candidate_at=candidate_at,
        )
