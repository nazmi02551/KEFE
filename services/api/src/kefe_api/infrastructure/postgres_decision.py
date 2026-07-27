from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import Engine, text

from kefe_api.modules.decision.models import (
    CaseVersion,
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

    def save_session(self, session: WeighSession) -> None:
        with self._engine.begin() as connection:
            self._save_session(connection, session)

    def save_session_with_event(
        self,
        session: WeighSession,
        *,
        event_name: str,
        payload: dict[str, object],
    ) -> None:
        with self._engine.begin() as connection:
            self._save_session(connection, session)
            self._append_event(connection, event_name, session.id, payload)

    def get_session(self, session_id: UUID) -> WeighSession | None:
        with self._engine.connect() as connection:
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

    def _save_session(self, connection, session: WeighSession) -> None:
        connection.execute(
            text(
                """
                INSERT INTO identity.actor (id, actor_kind, state)
                VALUES (:actor_id, 'GUEST', 'ACTIVE')
                ON CONFLICT (id) DO NOTHING
                """
            ),
            {"actor_id": session.actor_id},
        )
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
                ON CONFLICT (id) DO UPDATE SET
                    state = EXCLUDED.state,
                    committed_at = EXCLUDED.committed_at,
                    commit_idempotency_key = EXCLUDED.commit_idempotency_key,
                    updated_at = now()
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
        connection.execute(
            text("DELETE FROM decision.response WHERE session_id = :session_id"),
            {"session_id": session.id},
        )
        for question_id, value in session.responses.items():
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
                    """
                ),
                {
                    "id": uuid4(),
                    "session_id": session.id,
                    "question_version_id": question_id,
                    "value_json": json.dumps(value),
                },
            )

    def _append_event(
        self,
        connection,
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
