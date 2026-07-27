from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Connection, Engine, text
from sqlalchemy.exc import IntegrityError

from kefe_api.modules.decision.models import (
    CaseVersion,
    CommitAttempt,
    CommitStatus,
    DraftUpdateAttempt,
    DraftUpdateStatus,
    Question,
    RevealSnapshot,
    WeighSession,
    WeighState,
)


class PostgresDecisionRepository:
    """PostgreSQL adapter for the M0 DecisionRepository port."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_current_case_version(self, case_id: UUID) -> CaseVersion | None:
        with self._engine.connect() as connection:
            version_id = connection.execute(
                text(
                    """
                    SELECT id
                    FROM content.case_version
                    WHERE case_id = :case_id
                      AND status = 'PUBLISHED'
                    ORDER BY version_no DESC
                    LIMIT 1
                    """
                ),
                {"case_id": case_id},
            ).scalar_one_or_none()
        return self.get_case_version(version_id) if version_id else None

    def get_case_version(self, version_id: UUID) -> CaseVersion | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        cv.id,
                        cv.case_id,
                        cv.version_no,
                        cv.title,
                        cv.summary,
                        cv.accepts_weighs,
                        ci.base_format_code,
                        ci.primary_domain_code,
                        ci.content_risk
                    FROM content.case_version cv
                    JOIN content.case_item ci ON ci.id = cv.case_id
                    WHERE cv.id = :version_id
                    """
                ),
                {"version_id": version_id},
            ).mappings().one_or_none()
            if row is None:
                return None

            question_rows = connection.execute(
                text(
                    """
                    SELECT DISTINCT ON (q.id)
                        qv.id,
                        qv.prompt,
                        qv.response_type,
                        qv.response_schema
                    FROM content.issue i
                    JOIN content.question q ON q.issue_id = i.id
                    JOIN content.question_version qv ON qv.question_id = q.id
                    WHERE i.case_version_id = :version_id
                      AND qv.is_active = true
                    ORDER BY q.id, qv.version_no DESC
                    """
                ),
                {"version_id": version_id},
            ).mappings().all()

        questions = tuple(
            Question(
                id=question_row["id"],
                prompt=question_row["prompt"],
                response_type=question_row["response_type"],
                options=tuple((question_row["response_schema"] or {}).get("options", [])),
            )
            for question_row in question_rows
        )
        return CaseVersion(
            id=row["id"],
            case_id=row["case_id"],
            title=row["title"],
            summary=row["summary"],
            base_format=row["base_format_code"],
            primary_domain=row["primary_domain_code"],
            content_risk=row["content_risk"],
            version_no=row["version_no"],
            questions=questions,
            accepts_weighs=row["accepts_weighs"],
        )

    def save_session_with_event(
        self,
        session: WeighSession,
        *,
        event_name: str,
        payload: dict[str, object],
    ) -> None:
        with self._engine.begin() as connection:
            self._ensure_actor(connection, session.actor_id)
            connection.execute(
                text(
                    """
                    INSERT INTO decision.weigh_session (
                        id,
                        actor_id,
                        case_id,
                        case_version_id,
                        state,
                        started_at,
                        committed_at,
                        commit_idempotency_key,
                        updated_at
                    )
                    VALUES (
                        :id,
                        :actor_id,
                        :case_id,
                        :case_version_id,
                        :state,
                        :started_at,
                        :committed_at,
                        :commit_key,
                        now()
                    )
                    """
                ),
                {
                    "id": session.id,
                    "actor_id": session.actor_id,
                    "case_id": session.case_id,
                    "case_version_id": session.case_version_id,
                    "state": session.state.value,
                    "started_at": session.started_at,
                    "committed_at": session.committed_at,
                    "commit_key": session.commit_key,
                },
            )
            self._append_event(connection, event_name, session.id, payload)

    def get_session(self, session_id: UUID) -> WeighSession | None:
        with self._engine.connect() as connection:
            return self._load_session(connection, session_id=session_id)

    def update_draft_responses(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        responses: dict[UUID, Any],
    ) -> DraftUpdateAttempt:
        with self._engine.begin() as connection:
            row = self._lock_session(connection, actor_id=actor_id, session_id=session_id)
            if row is None:
                return DraftUpdateAttempt(DraftUpdateStatus.NOT_FOUND, None)
            if row["state"] != WeighState.DRAFT.value:
                session = self._load_session(connection, session_id=session_id)
                return DraftUpdateAttempt(DraftUpdateStatus.NOT_EDITABLE, session)

            for question_id, value in responses.items():
                connection.execute(
                    text(
                        """
                        INSERT INTO decision.response (
                            id,
                            session_id,
                            question_version_id,
                            value_json,
                            updated_at
                        )
                        VALUES (
                            :id,
                            :session_id,
                            :question_version_id,
                            CAST(:value_json AS jsonb),
                            now()
                        )
                        ON CONFLICT (session_id, question_version_id)
                        DO UPDATE SET
                            value_json = EXCLUDED.value_json,
                            updated_at = now()
                        """
                    ),
                    {
                        "id": uuid4(),
                        "session_id": session_id,
                        "question_version_id": question_id,
                        "value_json": json.dumps(value),
                    },
                )

            connection.execute(
                text(
                    """
                    UPDATE decision.weigh_session
                    SET updated_at = now()
                    WHERE id = :session_id
                    """
                ),
                {"session_id": session_id},
            )
            session = self._load_session(connection, session_id=session_id)
            return DraftUpdateAttempt(DraftUpdateStatus.UPDATED, session)

    def commit_session(
        self,
        *,
        actor_id: UUID,
        session_id: UUID,
        idempotency_key: str,
        required_question_ids: frozenset[UUID],
        committed_at: datetime,
    ) -> CommitAttempt:
        try:
            with self._engine.begin() as connection:
                return self._commit_session_in_transaction(
                    connection,
                    actor_id=actor_id,
                    session_id=session_id,
                    idempotency_key=idempotency_key,
                    required_question_ids=required_question_ids,
                    committed_at=committed_at,
                )
        except IntegrityError as exc:
            constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            session = self.get_session(session_id)
            if constraint_name == "commit_idempotency_actor_key_idx":
                return CommitAttempt(CommitStatus.IDEMPOTENCY_KEY_REUSED, session)
            if constraint_name == "committed_actor_case_version_idx":
                return CommitAttempt(CommitStatus.ALREADY_COMMITTED, session)
            raise

    def get_reveal(self, case_version_id: UUID) -> RevealSnapshot | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT case_version_id, layer, n, confidence_label, generated_at, payload
                    FROM analytics.result_snapshot
                    WHERE case_version_id = :case_version_id
                      AND layer = 'TRUSTED'
                    ORDER BY generated_at DESC
                    LIMIT 1
                    """
                ),
                {"case_version_id": case_version_id},
            ).mappings().one_or_none()
        if row is None:
            return None
        return RevealSnapshot(
            case_version_id=row["case_version_id"],
            layer=row["layer"],
            n=row["n"],
            confidence=row["confidence_label"],
            generated_at=row["generated_at"],
            payload=row["payload"],
        )

    def append_event(self, name: str, aggregate_id: UUID, payload: dict[str, object]) -> None:
        with self._engine.begin() as connection:
            self._append_event(connection, name, aggregate_id, payload)

    def _commit_session_in_transaction(
        self,
        connection: Connection,
        *,
        actor_id: UUID,
        session_id: UUID,
        idempotency_key: str,
        required_question_ids: frozenset[UUID],
        committed_at: datetime,
    ) -> CommitAttempt:
        row = self._lock_session(connection, actor_id=actor_id, session_id=session_id)
        if row is None:
            return CommitAttempt(CommitStatus.NOT_FOUND, None)

        session = self._load_session(connection, session_id=session_id)
        assert session is not None

        if session.state is WeighState.COMMITTED:
            status = (
                CommitStatus.IDEMPOTENT_REPLAY
                if session.commit_key == idempotency_key
                else CommitStatus.ALREADY_COMMITTED
            )
            return CommitAttempt(status, session)

        reused_key = connection.execute(
            text(
                """
                SELECT 1
                FROM decision.weigh_session
                WHERE actor_id = :actor_id
                  AND commit_idempotency_key = :idempotency_key
                  AND id <> :session_id
                LIMIT 1
                """
            ),
            {
                "actor_id": actor_id,
                "idempotency_key": idempotency_key,
                "session_id": session_id,
            },
        ).scalar_one_or_none()
        if reused_key:
            return CommitAttempt(CommitStatus.IDEMPOTENCY_KEY_REUSED, session)

        other_commit = connection.execute(
            text(
                """
                SELECT 1
                FROM decision.weigh_session
                WHERE actor_id = :actor_id
                  AND case_version_id = :case_version_id
                  AND state = 'COMMITTED'
                  AND id <> :session_id
                LIMIT 1
                """
            ),
            {
                "actor_id": actor_id,
                "case_version_id": session.case_version_id,
                "session_id": session_id,
            },
        ).scalar_one_or_none()
        if other_commit:
            return CommitAttempt(CommitStatus.ALREADY_COMMITTED, session)

        is_current = connection.execute(
            text(
                """
                SELECT 1
                FROM content.case_version
                WHERE id = :case_version_id
                  AND case_id = :case_id
                  AND status = 'PUBLISHED'
                  AND accepts_weighs = true
                LIMIT 1
                """
            ),
            {
                "case_version_id": session.case_version_id,
                "case_id": session.case_id,
            },
        ).scalar_one_or_none()
        if session.state is not WeighState.DRAFT or not is_current:
            connection.execute(
                text(
                    """
                    UPDATE decision.weigh_session
                    SET state = 'BLOCKED_BY_VERSION', updated_at = now()
                    WHERE id = :session_id
                      AND state <> 'COMMITTED'
                    """
                ),
                {"session_id": session_id},
            )
            session.state = WeighState.BLOCKED_BY_VERSION
            return CommitAttempt(CommitStatus.STALE_VERSION, session)

        answered = frozenset(
            connection.execute(
                text(
                    """
                    SELECT question_version_id
                    FROM decision.response
                    WHERE session_id = :session_id
                    """
                ),
                {"session_id": session_id},
            ).scalars()
        )
        missing = tuple(sorted(required_question_ids - answered, key=str))
        if missing:
            return CommitAttempt(CommitStatus.INCOMPLETE, session, missing)

        connection.execute(
            text(
                """
                UPDATE decision.weigh_session
                SET
                    state = 'COMMITTED',
                    committed_at = :committed_at,
                    commit_idempotency_key = :idempotency_key,
                    updated_at = now()
                WHERE id = :session_id
                  AND state = 'DRAFT'
                """
            ),
            {
                "session_id": session_id,
                "committed_at": committed_at,
                "idempotency_key": idempotency_key,
            },
        )
        self._append_event(
            connection,
            "weigh.committed",
            session_id,
            {
                "actor_id": str(actor_id),
                "case_version_id": str(session.case_version_id),
                "committed_at": committed_at.isoformat(),
            },
        )
        session.state = WeighState.COMMITTED
        session.commit_key = idempotency_key
        session.committed_at = committed_at
        return CommitAttempt(CommitStatus.COMMITTED, session)

    def _lock_session(
        self,
        connection: Connection,
        *,
        actor_id: UUID,
        session_id: UUID,
    ):
        return connection.execute(
            text(
                """
                SELECT
                    id,
                    actor_id,
                    case_id,
                    case_version_id,
                    state,
                    started_at,
                    committed_at,
                    commit_idempotency_key
                FROM decision.weigh_session
                WHERE id = :session_id
                  AND actor_id = :actor_id
                FOR UPDATE
                """
            ),
            {"session_id": session_id, "actor_id": actor_id},
        ).mappings().one_or_none()

    def _load_session(
        self,
        connection: Connection,
        *,
        session_id: UUID,
    ) -> WeighSession | None:
        row = connection.execute(
            text(
                """
                SELECT
                    id,
                    actor_id,
                    case_id,
                    case_version_id,
                    state,
                    started_at,
                    committed_at,
                    commit_idempotency_key
                FROM decision.weigh_session
                WHERE id = :session_id
                """
            ),
            {"session_id": session_id},
        ).mappings().one_or_none()
        if row is None:
            return None

        response_rows = connection.execute(
            text(
                """
                SELECT question_version_id, value_json
                FROM decision.response
                WHERE session_id = :session_id
                """
            ),
            {"session_id": session_id},
        ).mappings().all()
        return WeighSession(
            id=row["id"],
            actor_id=row["actor_id"],
            case_id=row["case_id"],
            case_version_id=row["case_version_id"],
            state=WeighState(row["state"]),
            responses={item["question_version_id"]: item["value_json"] for item in response_rows},
            started_at=row["started_at"],
            committed_at=row["committed_at"],
            commit_key=row["commit_idempotency_key"],
        )

    def _ensure_actor(self, connection: Connection, actor_id: UUID) -> None:
        connection.execute(
            text(
                """
                INSERT INTO identity.actor (id, actor_kind, state)
                VALUES (:actor_id, 'GUEST', 'ACTIVE')
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"actor_id": actor_id},
        )

    def _append_event(
        self,
        connection: Connection,
        name: str,
        aggregate_id: UUID,
        payload: dict[str, object],
    ) -> None:
        connection.execute(
            text(
                """
                INSERT INTO analytics.outbox_event (
                    id,
                    aggregate_type,
                    aggregate_id,
                    event_name,
                    event_version,
                    occurred_at,
                    payload,
                    created_at
                )
                VALUES (
                    :id,
                    'WEIGH_SESSION',
                    :aggregate_id,
                    :event_name,
                    1,
                    :occurred_at,
                    CAST(:payload AS jsonb),
                    now()
                )
                """
            ),
            {
                "id": uuid4(),
                "aggregate_id": aggregate_id,
                "event_name": name,
                "occurred_at": datetime.now(UTC),
                "payload": json.dumps(payload),
            },
        )
