from __future__ import annotations

from collections import Counter
from datetime import datetime
from types import MappingProxyType
from uuid import UUID

from kefe_api.modules.community_reason.models import (
    CommunityReason,
    CommunityReasonModeration,
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
        self._reports: set[tuple[UUID, UUID, ReasonReportCode]] = set()

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
        tag_counts: Counter[str] = Counter()
        rendered: list[PublicCommunityReason] = []
        for reason in public[:limit]:
            tag_counts.update(set(reason.tags))
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
        del report_id, created_at
        self._reports.add((reason_id, reporter_actor_id, report_code))

    def moderate(
        self,
        *,
        reason_id: UUID,
        state: CommunityReasonModeration,
        updated_at: datetime,
    ) -> CommunityReason | None:
        reason = self._reasons.get(reason_id)
        if reason is None:
            return None
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
        self._reasons[reason_id] = updated
        return updated
