from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, text
from sqlalchemy.exc import IntegrityError

from kefe_api.infrastructure.postgres_perspective_decision import (
    PostgresPerspectiveDecisionRepository,
)
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
from kefe_api.modules.decision.models import CommitAttempt, CommitStatus, WeighState


class PostgresDecisionLineageRepository(PostgresPerspectiveDecisionRepository):
    """Decision adapter with immutable revision/exposure/intervention lineage."""

    def commit_session(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        idempotency_key: str,
        required_question_ids: frozenset[UUID],
        committed_at: datetime,
        flow_step_code: str | None = None,
    ) -> CommitAttempt:
        try:
            with self._engine.begin() as connection:
                attempt = self._commit_session_in_transaction(
                    connection,
                    actor_id=actor_id,
                    session_id=session_id,
                    idempotency_key=idempotency_key,
                    required_question_ids=required_question_ids,
                    committed_at=committed_at,
                )
                if attempt.status is CommitStatus.COMMITTED and attempt.session is not None:
                    step_code = flow_step_code or self._initial_decision_step_code(
                        connection, attempt.session.case_version_id
                    )
                    self._insert_initial_revision(
                        connection,
                        session_id=session_id,
                        actor_id=actor_id,
                        case_version_id=attempt.session.case_version_id,
                        flow_step_code=step_code,
                        idempotency_key=idempotency_key,
                        committed_at=committed_at,
                    )
                return attempt
        except IntegrityError as exc:
            constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            session = self.get_session(session_id)
            if constraint_name == "commit_idempotency_actor_key_idx":
                return CommitAttempt(CommitStatus.IDEMPOTENCY_KEY_REUSED, session)
            if constraint_name == "committed_actor_case_version_idx":
                return CommitAttempt(CommitStatus.ALREADY_COMMITTED, session)
            raise

    def get_revision_draft(self, *, session_id: UUID, flow_step_code: str) -> RevisionDraft | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(
                        """
                    SELECT session_id, flow_step_code, response_snapshot,
                           private_reason_snapshot, updated_at
                    FROM decision.revision_draft
                    WHERE session_id = :session_id
                      AND flow_step_code = :flow_step_code
                    """
                    ),
                    {"session_id": session_id, "flow_step_code": flow_step_code},
                )
                .mappings()
                .one_or_none()
            )
        if row is None:
            return None
        return self._draft_from_row(row)

    def save_revision_draft(self, draft: RevisionDraft) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO decision.revision_draft (
                        session_id, flow_step_code, response_snapshot,
                        private_reason_snapshot, updated_at
                    ) VALUES (
                        :session_id, :flow_step_code, CAST(:responses AS jsonb),
                        CAST(:reason AS jsonb), :updated_at
                    )
                    ON CONFLICT (session_id, flow_step_code)
                    DO UPDATE SET
                        response_snapshot = EXCLUDED.response_snapshot,
                        private_reason_snapshot = EXCLUDED.private_reason_snapshot,
                        updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    "session_id": draft.session_id,
                    "flow_step_code": draft.flow_step_code,
                    "responses": json.dumps(
                        {str(key): value for key, value in draft.responses.items()}
                    ),
                    "reason": (
                        json.dumps(draft.reason_snapshot)
                        if draft.reason_snapshot is not None
                        else None
                    ),
                    "updated_at": draft.updated_at,
                },
            )

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
        with self._engine.begin() as connection:
            session_row = self._lock_session(connection, actor_id=actor_id, session_id=session_id)
            if session_row is None or session_row["case_version_id"] != case_version_id:
                raise ValueError("session ownership mismatch")

            existing = (
                connection.execute(
                    text(
                        """
                    SELECT * FROM decision.exposure
                    WHERE session_id = :session_id
                      AND idempotency_key = :idempotency_key
                    """
                    ),
                    {"session_id": session_id, "idempotency_key": idempotency_key},
                )
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                exposure = self._exposure_from_row(existing)
                intervention_row = (
                    connection.execute(
                        text(
                            """
                        SELECT * FROM decision.intervention
                        WHERE exposure_id = :exposure_id
                        """
                        ),
                        {"exposure_id": exposure.id},
                    )
                    .mappings()
                    .one_or_none()
                )
                return exposure, (
                    self._intervention_from_row(intervention_row)
                    if intervention_row is not None
                    else None
                )

            sequence_no = int(
                connection.execute(
                    text(
                        """
                        SELECT COALESCE(MAX(sequence_no), 0) + 1
                        FROM decision.exposure
                        WHERE session_id = :session_id
                        """
                    ),
                    {"session_id": session_id},
                ).scalar_one()
            )
            exposure_id = uuid4()
            connection.execute(
                text(
                    """
                    INSERT INTO decision.exposure (
                        id, session_id, actor_id, case_version_id, sequence_no,
                        flow_step_code, resource_category, resource_ref,
                        primitive_code, capability_codes, metadata,
                        idempotency_key, occurred_at
                    ) VALUES (
                        :id, :session_id, :actor_id, :case_version_id, :sequence_no,
                        :flow_step_code, :resource_category, :resource_ref,
                        :primitive_code, CAST(:capability_codes AS jsonb),
                        CAST(:metadata AS jsonb), :idempotency_key, :occurred_at
                    )
                    """
                ),
                {
                    "id": exposure_id,
                    "session_id": session_id,
                    "actor_id": actor_id,
                    "case_version_id": case_version_id,
                    "sequence_no": sequence_no,
                    "flow_step_code": flow_step_code,
                    "resource_category": resource_category,
                    "resource_ref": resource_ref,
                    "primitive_code": primitive_code,
                    "capability_codes": json.dumps(list(capability_codes)),
                    "metadata": json.dumps(metadata),
                    "idempotency_key": idempotency_key,
                    "occurred_at": occurred_at,
                },
            )
            exposure = Exposure(
                id=exposure_id,
                session_id=session_id,
                actor_id=actor_id,
                case_version_id=case_version_id,
                sequence_no=sequence_no,
                flow_step_code=flow_step_code,
                resource_category=resource_category,
                resource_ref=resource_ref,
                primitive_code=primitive_code,
                capability_codes=capability_codes,
                metadata=metadata,
                idempotency_key=idempotency_key,
                occurred_at=occurred_at,
            )

            intervention = None
            if intervention_type_code is not None:
                intervention = Intervention(
                    id=uuid4(),
                    session_id=session_id,
                    exposure_id=exposure.id,
                    type_code=intervention_type_code,
                    dimension_code=None,
                    metadata=intervention_metadata or {},
                    occurred_at=occurred_at,
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO decision.intervention (
                            id, session_id, exposure_id, type_code,
                            dimension_code, metadata, occurred_at
                        ) VALUES (
                            :id, :session_id, :exposure_id, :type_code,
                            NULL, CAST(:metadata AS jsonb), :occurred_at
                        )
                        """
                    ),
                    {
                        "id": intervention.id,
                        "session_id": session_id,
                        "exposure_id": exposure.id,
                        "type_code": intervention.type_code,
                        "metadata": json.dumps(intervention.metadata),
                        "occurred_at": occurred_at,
                    },
                )

            self._append_event(
                connection,
                "intervention.exposed" if intervention else "exposure.recorded",
                session_id,
                {
                    "flow_step_code": flow_step_code,
                    "resource_category": resource_category,
                    "exposure_id": str(exposure.id),
                    "intervention_id": str(intervention.id) if intervention else None,
                },
            )
            return exposure, intervention

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
        with self._engine.begin() as connection:
            session_row = self._lock_session(connection, actor_id=actor_id, session_id=session_id)
            if session_row is None or session_row["state"] != WeighState.COMMITTED.value:
                return RevisionCommitAttempt(RevisionCommitStatus.NOT_FOUND, None)

            existing_row = (
                connection.execute(
                    text(
                        """
                    SELECT * FROM decision.decision_revision
                    WHERE session_id = :session_id
                      AND flow_step_code = :flow_step_code
                    """
                    ),
                    {"session_id": session_id, "flow_step_code": flow_step_code},
                )
                .mappings()
                .one_or_none()
            )
            if existing_row is not None:
                revision = self._revision_from_row(existing_row)
                status = (
                    RevisionCommitStatus.IDEMPOTENT_REPLAY
                    if revision.commit_idempotency_key == idempotency_key
                    else RevisionCommitStatus.ALREADY_COMMITTED
                )
                return RevisionCommitAttempt(
                    status,
                    revision,
                    self._delta_for_revision(connection, revision.id),
                )

            reused = connection.execute(
                text(
                    """
                    SELECT 1 FROM decision.decision_revision
                    WHERE session_id = :session_id
                      AND commit_idempotency_key = :idempotency_key
                    LIMIT 1
                    """
                ),
                {"session_id": session_id, "idempotency_key": idempotency_key},
            ).scalar_one_or_none()
            if reused:
                return RevisionCommitAttempt(RevisionCommitStatus.IDEMPOTENCY_KEY_REUSED, None)

            draft_row = (
                connection.execute(
                    text(
                        """
                    SELECT * FROM decision.revision_draft
                    WHERE session_id = :session_id
                      AND flow_step_code = :flow_step_code
                    FOR UPDATE
                    """
                    ),
                    {"session_id": session_id, "flow_step_code": flow_step_code},
                )
                .mappings()
                .one_or_none()
            )
            draft = self._draft_from_row(draft_row) if draft_row is not None else None
            responses = draft.responses if draft else {}
            missing = tuple(sorted(required_question_ids - responses.keys(), key=str))
            if missing:
                return RevisionCommitAttempt(
                    RevisionCommitStatus.INCOMPLETE,
                    None,
                    missing_question_ids=missing,
                )

            previous_row = (
                connection.execute(
                    text(
                        """
                    SELECT * FROM decision.decision_revision
                    WHERE session_id = :session_id
                    ORDER BY revision_no DESC
                    LIMIT 1
                    """
                    ),
                    {"session_id": session_id},
                )
                .mappings()
                .one_or_none()
            )
            previous = self._revision_from_row(previous_row) if previous_row else None
            revision_no = (previous.revision_no + 1) if previous else 1
            exposure_sequence = int(
                connection.execute(
                    text(
                        """
                        SELECT COALESCE(MAX(sequence_no), 0)
                        FROM decision.exposure
                        WHERE session_id = :session_id
                        """
                    ),
                    {"session_id": session_id},
                ).scalar_one()
            )
            contribution = self._contribution_class(
                connection, session_id=session_id, sequence_no=exposure_sequence
            )
            revision = DecisionRevision(
                id=uuid4(),
                session_id=session_id,
                actor_id=actor_id,
                case_version_id=session_row["case_version_id"],
                revision_no=revision_no,
                flow_step_code=flow_step_code,
                responses=dict(responses),
                private_reason_snapshot=(draft.reason_snapshot if draft else None),
                exposure_sequence_at_commit=exposure_sequence,
                contribution_class=contribution,
                commit_idempotency_key=idempotency_key,
                committed_at=committed_at,
            )
            self._insert_revision(connection, revision)

            delta = None
            if previous is not None:
                intervention_rows = (
                    connection.execute(
                        text(
                            """
                        SELECT * FROM decision.intervention
                        WHERE session_id = :session_id
                          AND occurred_at > :after
                          AND occurred_at <= :until
                        ORDER BY occurred_at, id
                        """
                        ),
                        {
                            "session_id": session_id,
                            "after": previous.committed_at,
                            "until": committed_at,
                        },
                    )
                    .mappings()
                    .all()
                )
                interventions = tuple(self._intervention_from_row(row) for row in intervention_rows)
                delta = DecisionDelta(
                    id=uuid4(),
                    session_id=session_id,
                    from_revision_id=previous.id,
                    to_revision_id=revision.id,
                    intervention_ids=tuple(item.id for item in interventions),
                    diff_snapshot=self._diff(previous.responses, revision.responses),
                    created_at=committed_at,
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO decision.decision_delta (
                            id, session_id, from_revision_id, to_revision_id,
                            diff_snapshot, created_at
                        ) VALUES (
                            :id, :session_id, :from_revision_id, :to_revision_id,
                            CAST(:diff_snapshot AS jsonb), :created_at
                        )
                        """
                    ),
                    {
                        "id": delta.id,
                        "session_id": session_id,
                        "from_revision_id": previous.id,
                        "to_revision_id": revision.id,
                        "diff_snapshot": json.dumps(delta.diff_snapshot),
                        "created_at": delta.created_at,
                    },
                )
                for intervention in interventions:
                    connection.execute(
                        text(
                            """
                            INSERT INTO decision.decision_delta_intervention (
                                decision_delta_id, intervention_id
                            ) VALUES (:delta_id, :intervention_id)
                            """
                        ),
                        {"delta_id": delta.id, "intervention_id": intervention.id},
                    )

            connection.execute(
                text(
                    """
                    DELETE FROM decision.revision_draft
                    WHERE session_id = :session_id
                      AND flow_step_code = :flow_step_code
                    """
                ),
                {"session_id": session_id, "flow_step_code": flow_step_code},
            )
            self._append_event(
                connection,
                "decision.revised",
                session_id,
                {
                    "revision_id": str(revision.id),
                    "revision_no": revision.revision_no,
                    "flow_step_code": flow_step_code,
                    "delta_id": str(delta.id) if delta else None,
                },
            )
            return RevisionCommitAttempt(RevisionCommitStatus.COMMITTED, revision, delta)

    def list_decision_revisions(self, session_id: UUID) -> tuple[DecisionRevision, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                    SELECT * FROM decision.decision_revision
                    WHERE session_id = :session_id
                    ORDER BY revision_no
                    """
                    ),
                    {"session_id": session_id},
                )
                .mappings()
                .all()
            )
        return tuple(self._revision_from_row(row) for row in rows)

    def list_exposures(self, session_id: UUID) -> tuple[Exposure, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                    SELECT * FROM decision.exposure
                    WHERE session_id = :session_id
                    ORDER BY sequence_no
                    """
                    ),
                    {"session_id": session_id},
                )
                .mappings()
                .all()
            )
        return tuple(self._exposure_from_row(row) for row in rows)

    def list_interventions(self, session_id: UUID) -> tuple[Intervention, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                    SELECT * FROM decision.intervention
                    WHERE session_id = :session_id
                    ORDER BY occurred_at, id
                    """
                    ),
                    {"session_id": session_id},
                )
                .mappings()
                .all()
            )
        return tuple(self._intervention_from_row(row) for row in rows)

    def list_decision_deltas(self, session_id: UUID) -> tuple[DecisionDelta, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                    SELECT * FROM decision.decision_delta
                    WHERE session_id = :session_id
                    ORDER BY created_at, id
                    """
                    ),
                    {"session_id": session_id},
                )
                .mappings()
                .all()
            )
            return tuple(self._delta_from_row(connection, row) for row in rows)

    def _insert_initial_revision(
        self,
        connection: Connection,
        *,
        session_id: UUID,
        actor_id: UUID,
        case_version_id: UUID,
        flow_step_code: str,
        idempotency_key: str,
        committed_at: datetime,
    ) -> None:
        exists = connection.execute(
            text(
                """
                SELECT 1 FROM decision.decision_revision
                WHERE session_id = :session_id AND revision_no = 1
                """
            ),
            {"session_id": session_id},
        ).scalar_one_or_none()
        if exists:
            return
        response_rows = (
            connection.execute(
                text(
                    """
                SELECT question_version_id, value_json
                FROM decision.response
                WHERE session_id = :session_id
                """
                ),
                {"session_id": session_id},
            )
            .mappings()
            .all()
        )
        reason_row = (
            connection.execute(
                text(
                    """
                SELECT tags, text_body, moderation_state, visibility
                FROM decision.private_reason
                WHERE session_id = :session_id
                """
                ),
                {"session_id": session_id},
            )
            .mappings()
            .one_or_none()
        )
        exposure_sequence = int(
            connection.execute(
                text(
                    """
                    SELECT COALESCE(MAX(sequence_no), 0)
                    FROM decision.exposure
                    WHERE session_id = :session_id
                    """
                ),
                {"session_id": session_id},
            ).scalar_one()
        )
        reason_snapshot = (
            {
                "tags": reason_row["tags"],
                "text": reason_row["text_body"],
                "moderation_state": reason_row["moderation_state"],
                "visibility": reason_row["visibility"],
            }
            if reason_row is not None
            else None
        )
        revision = DecisionRevision(
            id=uuid4(),
            session_id=session_id,
            actor_id=actor_id,
            case_version_id=case_version_id,
            revision_no=1,
            flow_step_code=flow_step_code,
            responses={row["question_version_id"]: row["value_json"] for row in response_rows},
            private_reason_snapshot=reason_snapshot,
            exposure_sequence_at_commit=exposure_sequence,
            contribution_class=self._contribution_class(
                connection, session_id=session_id, sequence_no=exposure_sequence
            ),
            commit_idempotency_key=idempotency_key,
            committed_at=committed_at,
        )
        self._insert_revision(connection, revision)

    @staticmethod
    def _initial_decision_step_code(connection: Connection, case_version_id: UUID) -> str:
        document = connection.execute(
            text("SELECT resolved_flow FROM content.case_version WHERE id = :id"),
            {"id": case_version_id},
        ).scalar_one_or_none()
        if isinstance(document, dict):
            for step in document.get("steps", []):
                if step.get("primitive_code") == "DECISION":
                    return str(step["code"])
        return "INITIAL_DECISION"

    @staticmethod
    def _insert_revision(connection: Connection, revision: DecisionRevision) -> None:
        connection.execute(
            text(
                """
                INSERT INTO decision.decision_revision (
                    id, session_id, actor_id, case_version_id, revision_no,
                    flow_step_code, response_snapshot, private_reason_snapshot,
                    exposure_sequence_at_commit, contribution_class,
                    commit_idempotency_key, committed_at
                ) VALUES (
                    :id, :session_id, :actor_id, :case_version_id, :revision_no,
                    :flow_step_code, CAST(:responses AS jsonb), CAST(:reason AS jsonb),
                    :exposure_sequence, :contribution_class,
                    :idempotency_key, :committed_at
                )
                """
            ),
            {
                "id": revision.id,
                "session_id": revision.session_id,
                "actor_id": revision.actor_id,
                "case_version_id": revision.case_version_id,
                "revision_no": revision.revision_no,
                "flow_step_code": revision.flow_step_code,
                "responses": json.dumps(
                    {str(key): value for key, value in revision.responses.items()}
                ),
                "reason": (
                    json.dumps(revision.private_reason_snapshot)
                    if revision.private_reason_snapshot is not None
                    else None
                ),
                "exposure_sequence": revision.exposure_sequence_at_commit,
                "contribution_class": revision.contribution_class.value,
                "idempotency_key": revision.commit_idempotency_key,
                "committed_at": revision.committed_at,
            },
        )

    @staticmethod
    def _contribution_class(
        connection: Connection, *, session_id: UUID, sequence_no: int
    ) -> ContributionClass:
        exposed = connection.execute(
            text(
                """
                SELECT 1 FROM decision.exposure
                WHERE session_id = :session_id
                  AND sequence_no <= :sequence_no
                  AND resource_category IN ('COLLECTIVE_RESULT','SIGNAL')
                LIMIT 1
                """
            ),
            {"session_id": session_id, "sequence_no": sequence_no},
        ).scalar_one_or_none()
        return ContributionClass.EXPOSED if exposed else ContributionClass.CORE_PRE_RESULT

    @staticmethod
    def _draft_from_row(row) -> RevisionDraft:
        return RevisionDraft(
            session_id=row["session_id"],
            flow_step_code=row["flow_step_code"],
            responses={UUID(key): value for key, value in (row["response_snapshot"] or {}).items()},
            reason_snapshot=row["private_reason_snapshot"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _revision_from_row(row) -> DecisionRevision:
        return DecisionRevision(
            id=row["id"],
            session_id=row["session_id"],
            actor_id=row["actor_id"],
            case_version_id=row["case_version_id"],
            revision_no=row["revision_no"],
            flow_step_code=row["flow_step_code"],
            responses={UUID(key): value for key, value in (row["response_snapshot"] or {}).items()},
            private_reason_snapshot=row["private_reason_snapshot"],
            exposure_sequence_at_commit=row["exposure_sequence_at_commit"],
            contribution_class=ContributionClass(row["contribution_class"]),
            commit_idempotency_key=row["commit_idempotency_key"],
            committed_at=row["committed_at"],
        )

    @staticmethod
    def _exposure_from_row(row) -> Exposure:
        return Exposure(
            id=row["id"],
            session_id=row["session_id"],
            actor_id=row["actor_id"],
            case_version_id=row["case_version_id"],
            sequence_no=row["sequence_no"],
            flow_step_code=row["flow_step_code"],
            resource_category=row["resource_category"],
            resource_ref=row["resource_ref"],
            primitive_code=row["primitive_code"],
            capability_codes=tuple(row["capability_codes"] or []),
            metadata=row["metadata"] or {},
            idempotency_key=row["idempotency_key"],
            occurred_at=row["occurred_at"],
        )

    @staticmethod
    def _intervention_from_row(row) -> Intervention:
        return Intervention(
            id=row["id"],
            session_id=row["session_id"],
            exposure_id=row["exposure_id"],
            type_code=row["type_code"],
            dimension_code=row["dimension_code"],
            metadata=row["metadata"] or {},
            occurred_at=row["occurred_at"],
        )

    def _delta_for_revision(
        self, connection: Connection, revision_id: UUID
    ) -> DecisionDelta | None:
        row = (
            connection.execute(
                text(
                    """
                SELECT * FROM decision.decision_delta
                WHERE to_revision_id = :revision_id
                """
                ),
                {"revision_id": revision_id},
            )
            .mappings()
            .one_or_none()
        )
        return self._delta_from_row(connection, row) if row is not None else None

    @staticmethod
    def _delta_from_row(connection: Connection, row) -> DecisionDelta:
        intervention_ids = tuple(
            connection.execute(
                text(
                    """
                    SELECT intervention_id
                    FROM decision.decision_delta_intervention
                    WHERE decision_delta_id = :delta_id
                    ORDER BY intervention_id
                    """
                ),
                {"delta_id": row["id"]},
            )
            .scalars()
            .all()
        )
        return DecisionDelta(
            id=row["id"],
            session_id=row["session_id"],
            from_revision_id=row["from_revision_id"],
            to_revision_id=row["to_revision_id"],
            intervention_ids=intervention_ids,
            diff_snapshot=row["diff_snapshot"] or {},
            created_at=row["created_at"],
        )

    @staticmethod
    def _diff(before: dict[UUID, Any], after: dict[UUID, Any]) -> dict[str, Any]:
        changed = sorted(
            str(question_id)
            for question_id in set(before) | set(after)
            if before.get(question_id) != after.get(question_id)
        )
        return {"changed_question_ids": changed, "changed_count": len(changed)}
