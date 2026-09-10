from __future__ import annotations

from uuid import UUID

from kefe_api.modules.impact.action_models import ActionMilestone
from kefe_api.modules.impact.models import (
    AuthorityVerificationStatus,
    InstitutionResponse,
)


class InMemoryImpactRepository:
    """In-memory implementation of ImpactRepository.

    Used in tests and memory persistence mode.
    Replaces the per-service plain-dict storage in service.py and action_service.py.
    Thread-safety is not guaranteed; intended for single-threaded use.
    """

    def __init__(self) -> None:
        self._responses: dict[UUID, InstitutionResponse] = {}
        self._actions: dict[UUID, ActionMilestone] = {}

    # ------------------------------------------------------------------
    # Institution Responses
    # ------------------------------------------------------------------

    def save_institution_response(self, response: InstitutionResponse) -> None:
        self._responses[response.response_id] = response

    def get_institution_response(self, response_id: UUID) -> InstitutionResponse | None:
        return self._responses.get(response_id)

    def list_verified_responses(self, case_version_id: UUID) -> list[InstitutionResponse]:
        results = [
            r for r in self._responses.values()
            if r.case_version_id == case_version_id
            and r.verification_status == AuthorityVerificationStatus.VERIFIED
        ]
        return sorted(results, key=lambda r: r.published_at, reverse=True)

    def list_all_responses(
        self,
        *,
        case_version_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[InstitutionResponse]:
        results = list(self._responses.values())
        if case_version_id is not None:
            results = [r for r in results if r.case_version_id == case_version_id]
        results.sort(key=lambda r: r.published_at, reverse=True)
        return results[offset : offset + limit]

    # ------------------------------------------------------------------
    # Action Milestones
    # ------------------------------------------------------------------

    def save_action(self, action: ActionMilestone) -> None:
        self._actions[action.action_id] = action

    def get_action(self, action_id: UUID) -> ActionMilestone | None:
        return self._actions.get(action_id)

    def update_action(self, action: ActionMilestone) -> None:
        if action.action_id not in self._actions:
            raise KeyError(f"Action {action.action_id} not found")
        self._actions[action.action_id] = action

    def list_actions(
        self,
        case_version_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActionMilestone]:
        results = [
            a for a in self._actions.values()
            if a.case_version_id == case_version_id
        ]
        results.sort(key=lambda a: a.created_at, reverse=True)
        return results[offset : offset + limit]

    def list_all_actions(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActionMilestone]:
        results = sorted(self._actions.values(), key=lambda a: a.created_at, reverse=True)
        return results[offset : offset + limit]