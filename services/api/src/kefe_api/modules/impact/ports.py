from __future__ import annotations

from typing import Protocol
from uuid import UUID

from kefe_api.modules.impact.action_models import ActionMilestone
from kefe_api.modules.impact.models import (
    InstitutionResponse,
)


class ImpactRepository(Protocol):
    """Hexagonal port for Impact persistence.

    Implementors: InMemoryImpactRepository (test/memory),
    PostgresImpactRepository (production).

    Invariants:
    - InstitutionResponses are publish-only; no deletion.
    - ActionMilestones are mutable only via update_action_progress().
    - Only VERIFIED responses are returned by list_verified_responses().
    - Impact data is always linked to a specific case_version_id.
    """

    # ------------------------------------------------------------------
    # Institution Responses
    # ------------------------------------------------------------------

    def save_institution_response(self, response: InstitutionResponse) -> None:
        """Persist a new institution response."""
        ...

    def get_institution_response(self, response_id: UUID) -> InstitutionResponse | None:
        """Retrieve a single institution response by its ID."""
        ...

    def list_verified_responses(self, case_version_id: UUID) -> list[InstitutionResponse]:
        """Return all VERIFIED institution responses for a CaseVersion, newest first."""
        ...

    def list_all_responses(
        self,
        *,
        case_version_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[InstitutionResponse]:
        """Return paginated institution responses, optionally filtered by case."""
        ...

    # ------------------------------------------------------------------
    # Action Milestones
    # ------------------------------------------------------------------

    def save_action(self, action: ActionMilestone) -> None:
        """Persist a new action milestone."""
        ...

    def get_action(self, action_id: UUID) -> ActionMilestone | None:
        """Retrieve a single action milestone by its ID."""
        ...

    def update_action(self, action: ActionMilestone) -> None:
        """Replace an existing action milestone (full update by action_id)."""
        ...

    def list_actions(
        self,
        case_version_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActionMilestone]:
        """Return action milestones for a CaseVersion, newest first."""
        ...

    def list_all_actions(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ActionMilestone]:
        """Return all action milestones paginated, newest first."""
        ...