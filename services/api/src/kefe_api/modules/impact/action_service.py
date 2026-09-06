from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from kefe_api.modules.impact.action_models import ActionMilestone, ActionStatus


class ActionFollowThroughService:
    def __init__(self) -> None:
        self._actions_by_case: dict[UUID, list[ActionMilestone]] = {}

    def propose_action(
        self,
        *,
        case_version_id: UUID,
        title: str,
        description: str,
        institution_response_id: UUID | None = None,
        target_completion_date: datetime | None = None,
    ) -> ActionMilestone:
        cleaned_title = title.strip()
        cleaned_desc = description.strip()

        if len(cleaned_title) < 3:
            raise ValueError("title must have at least 3 characters")
        if len(cleaned_desc) < 10:
            raise ValueError("description must have at least 10 characters")

        action = ActionMilestone(
            action_id=uuid4(),
            case_version_id=case_version_id,
            title=cleaned_title,
            description=cleaned_desc,
            status=ActionStatus.PROPOSED,
            progress_percentage=0,
            institution_response_id=institution_response_id,
            target_completion_date=target_completion_date,
            created_at=datetime.now(UTC),
        )

        self._actions_by_case.setdefault(case_version_id, []).append(action)
        return action

    def update_progress(
        self,
        *,
        case_version_id: UUID,
        action_id: UUID,
        progress_percentage: int,
        status: ActionStatus,
        evidence_summary: str | None = None,
        evidence_url: str | None = None,
    ) -> ActionMilestone:
        if not (0 <= progress_percentage <= 100):
            raise ValueError("progress_percentage must be between 0 and 100")

        actions = self._actions_by_case.get(case_version_id, [])
        for i, a in enumerate(actions):
            if a.action_id == action_id:
                updated = ActionMilestone(
                    action_id=a.action_id,
                    case_version_id=a.case_version_id,
                    title=a.title,
                    description=a.description,
                    status=status,
                    progress_percentage=progress_percentage,
                    institution_response_id=a.institution_response_id,
                    target_completion_date=a.target_completion_date,
                    created_at=a.created_at,
                    evidence_summary=evidence_summary,
                    evidence_url=evidence_url,
                )
                actions[i] = updated
                return updated

        raise KeyError(f"Action {action_id} not found for case {case_version_id}")

    def list_actions(self, case_version_id: UUID) -> list[ActionMilestone]:
        return list(self._actions_by_case.get(case_version_id, []))
