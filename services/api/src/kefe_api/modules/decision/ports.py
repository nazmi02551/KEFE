from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from kefe_api.modules.decision.lineage_models import (
    DecisionDelta,
    DecisionRevision,
    Exposure,
    Intervention,
    RevisionCommitAttempt,
    RevisionDraft,
)
from kefe_api.modules.decision.models import (
    CaseVersion,
    CommitAttempt,
    DraftUpdateAttempt,
    PerspectiveSnapshot,
    PublicCaseVersion,
    ReasonUpdateAttempt,
    RevealSnapshot,
    WeighSession,
)
from kefe_api.modules.decision.reflection_models import (
    ReflectionCompletion,
    ReflectionCompletionAttempt,
)


class DecisionRepository(Protocol):
    def list_current_cases(self, *, limit: int) -> tuple[CaseVersion, ...]: ...

    def list_public_case_versions(
        self,
        case_id: UUID,
        *,
        limit: int,
    ) -> tuple[PublicCaseVersion, ...]: ...

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
        flow_step_code: str | None = None,
    ) -> CommitAttempt: ...

    def get_revision_draft(
        self, *, session_id: UUID, flow_step_code: str
    ) -> RevisionDraft | None: ...

    def save_revision_draft(self, draft: RevisionDraft) -> None: ...

    def record_exposure(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        case_version_id: UUID,
        flow_step_code: str,
        resource_category: str,
        resource_ref: str | None,
        primitive_code: str,
        capability_codes: tuple[str, ...],
        metadata: dict[str, Any],
        idempotency_key: str,
        occurred_at: datetime,
        intervention_type_code: str | None = None,
        intervention_metadata: dict[str, Any] | None = None,
    ) -> tuple[Exposure, Intervention | None]: ...

    def commit_revision(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        flow_step_code: str,
        idempotency_key: str,
        required_question_ids: frozenset[UUID],
        committed_at: datetime,
    ) -> RevisionCommitAttempt: ...

    def list_decision_revisions(self, session_id: UUID) -> tuple[DecisionRevision, ...]: ...

    def list_exposures(self, session_id: UUID) -> tuple[Exposure, ...]: ...

    def list_interventions(self, session_id: UUID) -> tuple[Intervention, ...]: ...

    def list_decision_deltas(self, session_id: UUID) -> tuple[DecisionDelta, ...]: ...

    def list_reflection_completions(
        self, session_id: UUID
    ) -> tuple[ReflectionCompletion, ...]: ...

    def complete_reflection(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        case_version_id: UUID,
        flow_step_code: str,
        latest_revision_id: UUID,
        latest_delta_id: UUID | None,
        idempotency_key: str,
        completed_at: datetime,
    ) -> ReflectionCompletionAttempt: ...

    def get_reveal(self, case_version_id: UUID) -> RevealSnapshot | None: ...

    def get_perspective(self, case_version_id: UUID) -> PerspectiveSnapshot | None: ...

    def append_event(self, name: str, aggregate_id: UUID, payload: dict[str, object]) -> None: ...
