from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from kefe_api.modules.decision.models import (
    CaseVersion,
    CommitAttempt,
    DraftUpdateAttempt,
    PerspectiveSnapshot,
    ReasonUpdateAttempt,
    RevealSnapshot,
    WeighSession,
)


class DecisionRepository(Protocol):
    def list_current_cases(self, *, limit: int) -> tuple[CaseVersion, ...]: ...

    def get_current_case_version(self, case_id: UUID) -> CaseVersion | None: ...

    def get_case_version(self, version_id: UUID) -> CaseVersion | None: ...

    def save_session_with_event(
        self,
        session: WeighSession,
        *,
        event_name: str,
        payload: dict[str, object],
    ) -> None: ...

    def get_session(self, session_id: UUID) -> WeighSession | None: ...

    def update_draft_responses(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        responses: dict[UUID, Any],
    ) -> DraftUpdateAttempt: ...

    def update_private_reason(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        tags: tuple[str, ...],
        text: str | None,
        updated_at: datetime,
    ) -> ReasonUpdateAttempt: ...

    def commit_session(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        idempotency_key: str,
        required_question_ids: frozenset[UUID],
        committed_at: datetime,
    ) -> CommitAttempt: ...

    def get_reveal(self, case_version_id: UUID) -> RevealSnapshot | None: ...

    def get_perspective(self, case_version_id: UUID) -> PerspectiveSnapshot | None: ...

    def append_event(self, name: str, aggregate_id: UUID, payload: dict[str, object]) -> None: ...
