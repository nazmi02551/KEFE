from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import UUID, uuid4

from kefe_api.modules.decision.lineage_models import (
    ContributionClass,
    DecisionDelta,
    DecisionRevision,
    Exposure,
    Intervention,
    RevisionCommitAttempt,
    RevisionCommitStatus,
    RevisionDraft,
)
from kefe_api.modules.decision.models import (
    CaseVersion,
    CommitAttempt,
    CommitStatus,
    DraftUpdateAttempt,
    DraftUpdateStatus,
    PerspectiveSnapshot,
    PrivateReason,
    ReasonModerationState,
    ReasonUpdateAttempt,
    RevealSnapshot,
    WeighSession,
    WeighState,
)


class InMemoryDecisionRepository:
    def __init__(
        self,
        *,
        cases: list[CaseVersion],
        reveals: list[RevealSnapshot],
        perspectives: list[PerspectiveSnapshot] | None = None,
    ) -> None:
        self._cases = {case.id: case for case in cases}
        self._current_by_case = {case.case_id: case.id for case in cases}
        self._sessions: dict[UUID, WeighSession] = {}
        self._reasons: dict[UUID, PrivateReason] = {}
        self._revision_drafts: dict[tuple[UUID, str], RevisionDraft] = {}
        self._revisions: dict[UUID, list[DecisionRevision]] = {}
        self._exposures: dict[UUID, list[Exposure]] = {}
        self._interventions: dict[UUID, list[Intervention]] = {}
        self._deltas: dict[UUID, list[DecisionDelta]] = {}
        self._reveals = {snapshot.case_version_id: snapshot for snapshot in reveals}
        self._perspectives = {
            snapshot.case_version_id: snapshot for snapshot in (perspectives or [])
        }
        self.events: list[dict[str, Any]] = []
        self._lock = RLock()

    def list_current_cases(self, *, limit: int) -> tuple[CaseVersion, ...]:
        with self._lock:
            current = [
                self._cases[version_id]
                for version_id in self._current_by_case.values()
                if version_id in self._cases
            ]
            current.sort(key=lambda case: (case.content_risk, case.title, str(case.case_id)))
            return tuple(current[:limit])

    def get_current_case_version(self, case_id: UUID) -> CaseVersion | None:
        with self._lock:
            version_id = self._current_by_case.get(case_id)
            return self._cases.get(version_id) if version_id else None

    def get_case_version(self, version_id: UUID) -> CaseVersion | None:
        with self._lock:
            return self._cases.get(version_id)

    def list_actor_committed_sessions(self, actor_id: UUID) -> tuple[WeighSession, ...]:
        with self._lock:
            sessions = [
                deepcopy(session)
                for session in self._sessions.values()
                if session.actor_id == actor_id and session.state is WeighState.COMMITTED
            ]
            return tuple(sessions)

    def save_session_with_event(
        self,
        session: WeighSession,
        *,
        event_name: str,
        payload: dict[str, object],
    ) -> None:
        with self._lock:
            self._sessions[session.id] = deepcopy(session)
            self._append_event(event_name, session.id, payload)

    def get_session(self, session_id: UUID) -> WeighSession | None:
        with self._lock:
            session = self._sessions.get(session_id)
            return deepcopy(session) if session else None

    def update_draft_responses(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        responses: dict[UUID, Any],
    ) -> DraftUpdateAttempt:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.actor_id != actor_id:
                return DraftUpdateAttempt(DraftUpdateStatus.NOT_FOUND, None)
            if session.state is not WeighState.DRAFT:
                return DraftUpdateAttempt(DraftUpdateStatus.NOT_EDITABLE, deepcopy(session))
            session.responses.update(responses)
            return DraftUpdateAttempt(DraftUpdateStatus.UPDATED, deepcopy(session))

    def update_private_reason(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        tags: tuple[str, ...],
        text: str | None,
        updated_at: datetime,
    ) -> ReasonUpdateAttempt:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.actor_id != actor_id:
                return ReasonUpdateAttempt(DraftUpdateStatus.NOT_FOUND, None)
            if session.state is not WeighState.DRAFT:
                return ReasonUpdateAttempt(
                    DraftUpdateStatus.NOT_EDITABLE,
                    deepcopy(self._reasons.get(session_id)),
                )
            reason = PrivateReason(
                session_id=session_id,
                tags=tags,
                text=text,
                moderation_state=(
                    ReasonModerationState.PENDING
                    if text is not None
                    else ReasonModerationState.NOT_REQUIRED
                ),
                updated_at=updated_at,
            )
            self._reasons[session_id] = reason
            return ReasonUpdateAttempt(DraftUpdateStatus.UPDATED, deepcopy(reason))

    def commit_session(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        idempotency_key: str,
        required_question_ids: frozenset[UUID],
        flow_step_code: str,
        committed_at: datetime,
    ) -> CommitAttempt:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.actor_id != actor_id:
                return CommitAttempt(CommitStatus.NOT_FOUND, None)

            for other in self._sessions.values():
                if (
                    other.id != session_id
                    and other.actor_id == actor_id
                    and other.commit_key == idempotency_key
                ):
                    return CommitAttempt(CommitStatus.IDEMPOTENCY_KEY_REUSED, deepcopy(session))

            if session.state is WeighState.COMMITTED:
                status = (
                    CommitStatus.IDEMPOTENT_REPLAY
                    if session.commit_key == idempotency_key
                    else CommitStatus.ALREADY_COMMITTED
                )
                return CommitAttempt(status, deepcopy(session))

            current_id = self._current_by_case.get(session.case_id)
            current = self._cases.get(current_id) if current_id else None
            if (
                session.state is not WeighState.DRAFT
                or current is None
                or current.id != session.case_version_id
                or not current.accepts_weighs
            ):
                session.state = WeighState.BLOCKED_BY_VERSION
                return CommitAttempt(CommitStatus.STALE_VERSION, deepcopy(session))

            missing = tuple(sorted(required_question_ids - session.responses.keys(), key=str))
            if missing:
                return CommitAttempt(CommitStatus.INCOMPLETE, deepcopy(session), missing)

            session.state = WeighState.COMMITTED
            session.commit_key = idempotency_key
            session.committed_at = committed_at
            self._materialize_initial_revision(
                session=session,
                flow_step_code=flow_step_code,
                idempotency_key=idempotency_key,
                committed_at=committed_at,
            )
            self._append_event(
                "weigh.committed",
                session.id,
                {
                    "actor_id": str(actor_id),
                    "case_version_id": str(session.case_version_id),
                    "committed_at": committed_at.isoformat(),
                    "has_reason": session.id in self._reasons,
                },
            )
            return CommitAttempt(CommitStatus.COMMITTED, deepcopy(session))

    def get_revision_draft(
        self, *, session_id: UUID, flow_step_code: str
    ) -> RevisionDraft | None:
        with self._lock:
            draft = self._revision_drafts.get((session_id, flow_step_code))
            return deepcopy(draft) if draft else None

    def save_revision_draft(self, draft: RevisionDraft) -> None:
        with self._lock:
            self._revision_drafts[(draft.session_id, draft.flow_step_code)] = deepcopy(draft)

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
    ) -> tuple[Exposure, Intervention | None]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.actor_id != actor_id or session.case_version_id != case_version_id:
                raise ValueError("session ownership mismatch")
            exposures = self._exposures.setdefault(session_id, [])
            existing = next(
                (item for item in exposures if item.idempotency_key == idempotency_key),
                None,
            )
            if existing is not None:
                intervention = next(
                    (
                        item
                        for item in self._interventions.get(session_id, [])
                        if item.exposure_id == existing.id
                    ),
                    None,
                )
                return deepcopy(existing), deepcopy(intervention)

            exposure = Exposure(
                id=uuid4(),
                session_id=session_id,
                actor_id=actor_id,
                case_version_id=case_version_id,
                sequence_no=len(exposures) + 1,
                flow_step_code=flow_step_code,
                resource_category=resource_category,
                resource_ref=resource_ref,
                primitive_code=primitive_code,
                capability_codes=capability_codes,
                metadata=deepcopy(metadata),
                idempotency_key=idempotency_key,
                occurred_at=occurred_at,
            )
            exposures.append(exposure)

            intervention = None
            if intervention_type_code is not None:
                intervention = Intervention(
                    id=uuid4(),
                    session_id=session_id,
                    exposure_id=exposure.id,
                    type_code=intervention_type_code,
                    dimension_code=None,
                    metadata=deepcopy(intervention_metadata or {}),
                    occurred_at=occurred_at,
                )
                self._interventions.setdefault(session_id, []).append(intervention)

            self._append_event(
                "intervention.exposed" if intervention else "exposure.recorded",
                session_id,
                {
                    "flow_step_code": flow_step_code,
                    "resource_category": resource_category,
                    "exposure_id": str(exposure.id),
                    "intervention_id": str(intervention.id) if intervention else None,
                },
            )
            return deepcopy(exposure), deepcopy(intervention)

    def commit_revision(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        flow_step_code: str,
        idempotency_key: str,
        required_question_ids: frozenset[UUID],
        committed_at: datetime,
    ) -> RevisionCommitAttempt:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or session.actor_id != actor_id:
                return RevisionCommitAttempt(RevisionCommitStatus.NOT_FOUND, None)
            revisions = self._revisions.setdefault(session_id, [])
            existing = next(
                (item for item in revisions if item.flow_step_code == flow_step_code),
                None,
            )
            if existing is not None:
                status = (
                    RevisionCommitStatus.IDEMPOTENT_REPLAY
                    if existing.commit_idempotency_key == idempotency_key
                    else RevisionCommitStatus.ALREADY_COMMITTED
                )
                delta = next(
                    (item for item in self._deltas.get(session_id, []) if item.to_revision_id == existing.id),
                    None,
                )
                return RevisionCommitAttempt(status, deepcopy(existing), deepcopy(delta))
            if any(item.commit_idempotency_key == idempotency_key for item in revisions):
                return RevisionCommitAttempt(RevisionCommitStatus.IDEMPOTENCY_KEY_REUSED, None)

            draft = self._revision_drafts.get((session_id, flow_step_code))
            responses = draft.responses if draft else {}
            missing = tuple(sorted(required_question_ids - responses.keys(), key=str))
            if missing:
                return RevisionCommitAttempt(
                    RevisionCommitStatus.INCOMPLETE,
                    None,
                    missing_question_ids=missing,
                )

            exposure_sequence = max(
                (item.sequence_no for item in self._exposures.get(session_id, [])),
                default=0,
            )
            contribution = self._contribution_class(session_id, exposure_sequence)
            revision = DecisionRevision(
                id=uuid4(),
                session_id=session_id,
                actor_id=actor_id,
                case_version_id=session.case_version_id,
                revision_no=len(revisions) + 1,
                flow_step_code=flow_step_code,
                responses=deepcopy(responses),
                private_reason_snapshot=deepcopy(draft.reason_snapshot) if draft else None,
                exposure_sequence_at_commit=exposure_sequence,
                contribution_class=contribution,
                commit_idempotency_key=idempotency_key,
                committed_at=committed_at,
            )
            previous = revisions[-1] if revisions else None
            revisions.append(revision)
            self._revision_drafts.pop((session_id, flow_step_code), None)

            delta = None
            if previous is not None:
                intervention_ids = tuple(
                    item.id
                    for item in self._interventions.get(session_id, [])
                    if previous.committed_at < item.occurred_at <= committed_at
                )
                delta = DecisionDelta(
                    id=uuid4(),
                    session_id=session_id,
                    from_revision_id=previous.id,
                    to_revision_id=revision.id,
                    intervention_ids=intervention_ids,
                    diff_snapshot=self._diff(previous.responses, revision.responses),
                    created_at=committed_at,
                )
                self._deltas.setdefault(session_id, []).append(delta)

            self._append_event(
                "decision.revised",
                session_id,
                {
                    "revision_id": str(revision.id),
                    "revision_no": revision.revision_no,
                    "flow_step_code": flow_step_code,
                    "delta_id": str(delta.id) if delta else None,
                },
            )
            return RevisionCommitAttempt(
                RevisionCommitStatus.COMMITTED,
                deepcopy(revision),
                deepcopy(delta),
            )

    def list_decision_revisions(self, session_id: UUID) -> tuple[DecisionRevision, ...]:
        with self._lock:
            return tuple(deepcopy(self._revisions.get(session_id, [])))

    def list_exposures(self, session_id: UUID) -> tuple[Exposure, ...]:
        with self._lock:
            return tuple(deepcopy(self._exposures.get(session_id, [])))

    def list_interventions(self, session_id: UUID) -> tuple[Intervention, ...]:
        with self._lock:
            return tuple(deepcopy(self._interventions.get(session_id, [])))

    def list_decision_deltas(self, session_id: UUID) -> tuple[DecisionDelta, ...]:
        with self._lock:
            return tuple(deepcopy(self._deltas.get(session_id, [])))

    def get_reveal(self, case_version_id: UUID) -> RevealSnapshot | None:
        with self._lock:
            return deepcopy(self._reveals.get(case_version_id))

    def get_perspective(self, case_version_id: UUID) -> PerspectiveSnapshot | None:
        with self._lock:
            return deepcopy(self._perspectives.get(case_version_id))

    def append_event(self, name: str, aggregate_id: UUID, payload: dict[str, object]) -> None:
        with self._lock:
            self._append_event(name, aggregate_id, payload)

    def _materialize_initial_revision(
        self,
        *,
        session: WeighSession,
        flow_step_code: str,
        idempotency_key: str,
        committed_at: datetime,
    ) -> None:
        if self._revisions.get(session.id):
            return
        exposure_sequence = max(
            (item.sequence_no for item in self._exposures.get(session.id, [])),
            default=0,
        )
        reason = self._reasons.get(session.id)
        reason_snapshot = (
            {
                "tags": list(reason.tags),
                "text": reason.text,
                "moderation_state": reason.moderation_state.value,
                "visibility": reason.visibility.value,
            }
            if reason is not None
            else None
        )
        revision = DecisionRevision(
            id=uuid4(),
            session_id=session.id,
            actor_id=session.actor_id,
            case_version_id=session.case_version_id,
            revision_no=1,
            flow_step_code=flow_step_code,
            responses=deepcopy(session.responses),
            private_reason_snapshot=reason_snapshot,
            exposure_sequence_at_commit=exposure_sequence,
            contribution_class=self._contribution_class(session.id, exposure_sequence),
            commit_idempotency_key=idempotency_key,
            committed_at=committed_at,
        )
        self._revisions.setdefault(session.id, []).append(revision)

    def _contribution_class(self, session_id: UUID, sequence_no: int) -> ContributionClass:
        exposed = any(
            item.sequence_no <= sequence_no
            and item.resource_category in {"COLLECTIVE_RESULT", "SIGNAL"}
            for item in self._exposures.get(session_id, [])
        )
        return ContributionClass.EXPOSED if exposed else ContributionClass.CORE_PRE_RESULT

    @staticmethod
    def _diff(before: dict[UUID, Any], after: dict[UUID, Any]) -> dict[str, Any]:
        changed = sorted(
            str(question_id)
            for question_id in set(before) | set(after)
            if before.get(question_id) != after.get(question_id)
        )
        return {"changed_question_ids": changed, "changed_count": len(changed)}

    def _append_event(
        self,
        name: str,
        aggregate_id: UUID,
        payload: dict[str, object],
    ) -> None:
        self.events.append(
            {
                "name": name,
                "aggregate_id": str(aggregate_id),
                "payload": payload,
                "occurred_at": datetime.now(UTC).isoformat(),
            }
        )
