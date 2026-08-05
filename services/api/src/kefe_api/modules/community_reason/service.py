from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.community_reason.models import (
    CommunityReason,
    CommunityReasonModeration,
    CommunityReasonModerationAudit,
    CommunityReasonModerationDecision,
    CommunityReasonModerationItem,
    CommunityReasonModerationQueueKind,
    CommunityReasonModerationWriteStatus,
    CommunityReasonSnapshot,
    ReasonReaction,
    ReasonReportCode,
)
from kefe_api.modules.community_reason.ports import CommunityReasonRepository
from kefe_api.modules.decision.models import Question, WeighState
from kefe_api.modules.decision.ports import DecisionRepository


class CommunityReasonService:
    def __init__(
        self,
        *,
        repository: CommunityReasonRepository,
        decision_repository: DecisionRepository,
    ) -> None:
        self._repo = repository
        self._decision = decision_repository

    def publish(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        tags: list[str],
        body: str | None,
    ) -> CommunityReason:
        session = self._decision.get_session(session_id)
        if session is None or session.actor_id != actor_id:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        if session.state is not WeighState.COMMITTED:
            raise DomainError(
                "COMMUNITY_REASON_COMMIT_REQUIRED",
                "Commit is required before publishing a Community Reason",
                403,
            )
        case = self._decision.get_case_version(session.case_version_id)
        if case is None:
            raise DomainError("CASE_VERSION_STALE", "Case version is no longer available", 409)
        policy = self._reason_policy(case.questions)
        if policy is None:
            raise DomainError(
                "COMMUNITY_REASON_NOT_SUPPORTED",
                "Reason tags are not configured",
                422,
            )

        allowed_tags = {
            str(tag).strip().upper() for tag in policy.get("tags", ()) if str(tag).strip()
        }
        normalized_tags = tuple(dict.fromkeys(tag.strip().upper() for tag in tags if tag.strip()))
        if not normalized_tags:
            raise DomainError(
                "COMMUNITY_REASON_EMPTY",
                "At least one reason tag is required",
                422,
            )
        unknown = [tag for tag in normalized_tags if tag not in allowed_tags]
        if unknown:
            raise DomainError(
                "COMMUNITY_REASON_TAG_INVALID",
                "Community Reason contains unsupported tags",
                422,
                meta={"unknown_tags": unknown},
            )
        max_tags = min(max(int(policy.get("max_tags", 3)), 1), 5)
        if len(normalized_tags) > max_tags:
            raise DomainError(
                "COMMUNITY_REASON_TAG_LIMIT_EXCEEDED",
                "Too many Community Reason tags",
                422,
                meta={"max_tags": max_tags},
            )
        normalized_body = body.strip() if body is not None else None
        if normalized_body == "":
            normalized_body = None
        if normalized_body is not None and len(normalized_body) > 300:
            raise DomainError(
                "COMMUNITY_REASON_TEXT_TOO_LONG",
                "Community Reason text exceeds the MVP limit",
                422,
                meta={"max_length": 300},
            )

        now = datetime.now(UTC)
        reason = self._repo.create_or_replace(
            CommunityReason(
                id=uuid4(),
                actor_id=actor_id,
                session_id=session.id,
                case_version_id=session.case_version_id,
                tags=normalized_tags,
                body=normalized_body,
                moderation_state=(
                    CommunityReasonModeration.PENDING
                    if normalized_body is not None
                    else CommunityReasonModeration.NOT_REQUIRED
                ),
                created_at=now,
                updated_at=now,
            )
        )
        self._decision.append_event(
            "community_reason.submitted",
            session.id,
            {
                "reason_id": str(reason.id),
                "case_version_id": str(reason.case_version_id),
                "tag_codes": list(reason.tags),
                "tag_count": len(reason.tags),
                "has_text": reason.body is not None,
                "moderation_state": reason.moderation_state.value,
            },
        )
        return reason

    def snapshot(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        limit: int = 20,
    ) -> CommunityReasonSnapshot:
        session = self._decision.get_session(session_id)
        if session is None or session.actor_id != actor_id:
            raise DomainError("WEIGH_SESSION_NOT_FOUND", "Weigh session not found", 404)
        if session.state is not WeighState.COMMITTED:
            raise DomainError(
                "COMMUNITY_REASON_COMMIT_REQUIRED",
                "Commit is required before reading Community Reasons",
                403,
            )
        case = self._decision.get_case_version(session.case_version_id)
        if case is None:
            raise DomainError("CASE_VERSION_STALE", "Case version is no longer available", 409)
        return self._repo.public_snapshot(
            session.case_version_id,
            limit=min(max(limit, 1), 50),
        )

    def react(
        self,
        *,
        actor_id: UUID,
        reason_id: UUID,
        reaction: ReasonReaction,
    ) -> None:
        reason = self._repo.get(reason_id)
        if reason is None or not reason.publicly_readable:
            raise DomainError(
                "COMMUNITY_REASON_NOT_FOUND",
                "Community Reason not found",
                404,
            )
        if reason.actor_id == actor_id:
            raise DomainError(
                "COMMUNITY_REASON_SELF_REACTION",
                "A user cannot react to their own Community Reason",
                409,
            )
        self._repo.set_reaction(
            reason_id=reason_id,
            actor_id=actor_id,
            reaction=reaction,
            created_at=datetime.now(UTC),
        )

    def report(
        self,
        *,
        actor_id: UUID,
        reason_id: UUID,
        report_code: ReasonReportCode,
    ) -> None:
        reason = self._repo.get(reason_id)
        if reason is None:
            raise DomainError(
                "COMMUNITY_REASON_NOT_FOUND",
                "Community Reason not found",
                404,
            )
        self._repo.report(
            report_id=uuid4(),
            reason_id=reason_id,
            reporter_actor_id=actor_id,
            report_code=report_code,
            created_at=datetime.now(UTC),
        )

    def moderation_queue(
        self,
        *,
        kind: CommunityReasonModerationQueueKind,
        limit: int = 25,
        offset: int = 0,
        case_version_id: UUID | None = None,
        report_code: ReasonReportCode | None = None,
    ) -> tuple[CommunityReasonModerationItem, ...]:
        if not 1 <= limit <= 100:
            raise DomainError(
                "COMMUNITY_REASON_MODERATION_LIMIT_INVALID",
                "Moderation queue limit must be between 1 and 100",
                422,
            )
        if not 0 <= offset <= 10000:
            raise DomainError(
                "COMMUNITY_REASON_MODERATION_OFFSET_INVALID",
                "Moderation queue offset must be between 0 and 10000",
                422,
            )
        return self._repo.moderation_queue(
            kind=kind,
            limit=limit,
            offset=offset,
            case_version_id=case_version_id,
            report_code=report_code,
        )

    def moderation_inspection(self, *, reason_id: UUID) -> CommunityReasonModerationItem:
        item = self._repo.moderation_inspection(reason_id)
        if item is None:
            raise DomainError(
                "COMMUNITY_REASON_NOT_FOUND",
                "Community Reason not found",
                404,
            )
        return item

    def moderation_audit(
        self,
        *,
        reason_id: UUID,
        limit: int = 100,
    ) -> tuple[CommunityReasonModerationAudit, ...]:
        if not 1 <= limit <= 100:
            raise DomainError(
                "COMMUNITY_REASON_MODERATION_AUDIT_LIMIT_INVALID",
                "Moderation audit limit must be between 1 and 100",
                422,
            )
        if self._repo.get(reason_id) is None:
            raise DomainError(
                "COMMUNITY_REASON_NOT_FOUND",
                "Community Reason not found",
                404,
            )
        return self._repo.moderation_audit(reason_id=reason_id, limit=limit)

    def moderate(
        self,
        *,
        reason_id: UUID,
        state: CommunityReasonModeration,
        actor_ref: str,
        rationale: str,
    ) -> CommunityReasonModerationDecision:
        if state not in {
            CommunityReasonModeration.ALLOWED,
            CommunityReasonModeration.BLOCKED,
        }:
            raise DomainError(
                "COMMUNITY_REASON_MODERATION_INVALID",
                "Invalid moderation state",
                422,
            )
        normalized_rationale = rationale.strip()
        if not 10 <= len(normalized_rationale) <= 1000:
            raise DomainError(
                "COMMUNITY_REASON_MODERATION_RATIONALE_INVALID",
                "Moderation rationale must be between 10 and 1000 characters",
                422,
            )
        result = self._repo.moderate(
            audit_id=uuid4(),
            reason_id=reason_id,
            state=state,
            actor_ref=actor_ref,
            rationale=normalized_rationale,
            updated_at=datetime.now(UTC),
        )
        if result.status is CommunityReasonModerationWriteStatus.NOT_FOUND:
            raise DomainError(
                "COMMUNITY_REASON_NOT_FOUND",
                "Community Reason not found",
                404,
            )
        if result.status is CommunityReasonModerationWriteStatus.CONFLICT:
            raise DomainError(
                "COMMUNITY_REASON_MODERATION_STATE_INVALID",
                "Community Reason cannot be moderated from its current state",
                409,
                meta={
                    "current_state": (
                        result.current_state.value if result.current_state is not None else None
                    )
                },
            )
        if result.decision is None:
            raise RuntimeError("Applied moderation result must include a decision")
        return result.decision

    @staticmethod
    def _reason_policy(questions: tuple[Question, ...]) -> Mapping[str, object] | None:
        for question in questions:
            raw = question.response_schema.get("reason")
            if isinstance(raw, Mapping):
                return raw
        return None
