from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.analytics.models import (
    ActivationJourney,
    AnalyticsEvent,
    AnalyticsPrivacyClass,
    AnalyticsRetentionClass,
)
from kefe_api.modules.analytics.service import ActivationJourneyProjector


class PostgresAnalyticsEventStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._journey_projector = ActivationJourneyProjector()

    def append_once(self, event: AnalyticsEvent) -> bool:
        with self._engine.begin() as connection:
            if self._journey_projector.supports(event):
                connection.execute(
                    text(
                        "SELECT pg_advisory_xact_lock("
                        "hashtextextended(CAST(:session_id AS text), 0))"
                    ),
                    {"session_id": event.session_id},
                )
            inserted = connection.execute(
                text(
                    """
                    INSERT INTO analytics.analytics_event (
                        id, source_event_id, source_event_name, source_event_version,
                        analytics_name, analytics_version, occurred_at, producer_version,
                        actor_id, session_id, case_version_id, contribution_class,
                        privacy_class, retention_class, metric_families, payload
                    ) VALUES (
                        :id, :source_event_id, :source_event_name, :source_event_version,
                        :analytics_name, :analytics_version, :occurred_at, :producer_version,
                        :actor_id, :session_id, :case_version_id, :contribution_class,
                        :privacy_class, :retention_class,
                        CAST(:metric_families AS jsonb), CAST(:payload AS jsonb)
                    )
                    ON CONFLICT (
                        source_event_id, analytics_name, analytics_version
                    ) DO NOTHING
                    RETURNING id
                    """
                ),
                {
                    "id": event.id,
                    "source_event_id": event.source_event_id,
                    "source_event_name": event.source_event_name,
                    "source_event_version": event.source_event_version,
                    "analytics_name": event.analytics_name,
                    "analytics_version": event.analytics_version,
                    "occurred_at": event.occurred_at,
                    "producer_version": event.producer_version,
                    "actor_id": event.actor_id,
                    "session_id": event.session_id,
                    "case_version_id": event.case_version_id,
                    "contribution_class": event.contribution_class,
                    "privacy_class": event.privacy_class.value,
                    "retention_class": event.retention_class.value,
                    "metric_families": json.dumps(
                        list(event.metric_families),
                        separators=(",", ":"),
                    ),
                    "payload": json.dumps(
                        event.payload,
                        separators=(",", ":"),
                        sort_keys=True,
                    ),
                },
            ).scalar_one_or_none()
            if inserted is not None and self._journey_projector.supports(event):
                current_row = (
                    connection.execute(
                        text(self._journey_select() + " WHERE session_id = :session_id"),
                        {"session_id": event.session_id},
                    )
                    .mappings()
                    .one_or_none()
                )
                current = (
                    None if current_row is None else self._activation_journey(current_row)
                )
                journey = self._journey_projector.apply(current, event)
                if journey is None:
                    raise RuntimeError("supported activation event did not produce a journey")
                connection.execute(
                    text(
                        """
                        INSERT INTO analytics.activation_journey (
                            session_id, actor_id, case_version_id,
                            started_at, started_source_event_id,
                            committed_at, committed_source_event_id,
                            result_revealed_at, result_revealed_source_event_id
                        ) VALUES (
                            :session_id, :actor_id, :case_version_id,
                            :started_at, :started_source_event_id,
                            :committed_at, :committed_source_event_id,
                            :result_revealed_at, :result_revealed_source_event_id
                        )
                        ON CONFLICT (session_id) DO UPDATE SET
                            actor_id = EXCLUDED.actor_id,
                            case_version_id = EXCLUDED.case_version_id,
                            started_at = EXCLUDED.started_at,
                            started_source_event_id = EXCLUDED.started_source_event_id,
                            committed_at = EXCLUDED.committed_at,
                            committed_source_event_id = EXCLUDED.committed_source_event_id,
                            result_revealed_at = EXCLUDED.result_revealed_at,
                            result_revealed_source_event_id =
                                EXCLUDED.result_revealed_source_event_id,
                            updated_at = now()
                        """
                    ),
                    {
                        "session_id": journey.session_id,
                        "actor_id": journey.actor_id,
                        "case_version_id": journey.case_version_id,
                        "started_at": journey.started_at,
                        "started_source_event_id": journey.started_source_event_id,
                        "committed_at": journey.committed_at,
                        "committed_source_event_id": journey.committed_source_event_id,
                        "result_revealed_at": journey.result_revealed_at,
                        "result_revealed_source_event_id": (
                            journey.result_revealed_source_event_id
                        ),
                    },
                )
        return inserted is not None

    def get(self, event_id: UUID) -> AnalyticsEvent | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(self._select() + " WHERE id = :event_id"),
                    {"event_id": event_id},
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else self._event(row)

    def list_by_source_event(
        self,
        source_event_id: UUID,
    ) -> tuple[AnalyticsEvent, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        self._select()
                        + " WHERE source_event_id = :source_event_id "
                        + "ORDER BY analytics_name, analytics_version"
                    ),
                    {"source_event_id": source_event_id},
                )
                .mappings()
                .all()
            )
        return tuple(self._event(row) for row in rows)

    def list_by_session(self, session_id: UUID) -> tuple[AnalyticsEvent, ...]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    text(
                        self._select()
                        + " WHERE session_id = :session_id "
                        + "ORDER BY occurred_at, source_event_id, analytics_name, "
                        + "analytics_version"
                    ),
                    {"session_id": session_id},
                )
                .mappings()
                .all()
            )
        return tuple(self._event(row) for row in rows)

    def get_activation_journey(self, session_id: UUID) -> ActivationJourney | None:
        with self._engine.connect() as connection:
            row = (
                connection.execute(
                    text(self._journey_select() + " WHERE session_id = :session_id"),
                    {"session_id": session_id},
                )
                .mappings()
                .one_or_none()
            )
        return None if row is None else self._activation_journey(row)

    @staticmethod
    def _select() -> str:
        return """
            SELECT
                id, source_event_id, source_event_name, source_event_version,
                analytics_name, analytics_version, occurred_at, producer_version,
                actor_id, session_id, case_version_id, contribution_class,
                privacy_class, retention_class, metric_families, payload
            FROM analytics.analytics_event
        """

    @staticmethod
    def _journey_select() -> str:
        return """
            SELECT
                session_id, actor_id, case_version_id,
                started_at, started_source_event_id,
                committed_at, committed_source_event_id,
                result_revealed_at, result_revealed_source_event_id
            FROM analytics.activation_journey
        """

    @staticmethod
    def _event(row) -> AnalyticsEvent:
        return AnalyticsEvent(
            id=row["id"],
            source_event_id=row["source_event_id"],
            source_event_name=row["source_event_name"],
            source_event_version=int(row["source_event_version"]),
            analytics_name=row["analytics_name"],
            analytics_version=int(row["analytics_version"]),
            occurred_at=row["occurred_at"],
            producer_version=row["producer_version"],
            actor_id=row["actor_id"],
            session_id=row["session_id"],
            case_version_id=row["case_version_id"],
            contribution_class=row["contribution_class"],
            privacy_class=AnalyticsPrivacyClass(row["privacy_class"]),
            retention_class=AnalyticsRetentionClass(row["retention_class"]),
            metric_families=tuple(row["metric_families"]),
            payload=dict(row["payload"]),
        )

    @staticmethod
    def _activation_journey(row) -> ActivationJourney:
        return ActivationJourney(
            session_id=row["session_id"],
            actor_id=row["actor_id"],
            case_version_id=row["case_version_id"],
            started_at=row["started_at"],
            started_source_event_id=row["started_source_event_id"],
            committed_at=row["committed_at"],
            committed_source_event_id=row["committed_source_event_id"],
            result_revealed_at=row["result_revealed_at"],
            result_revealed_source_event_id=row[
                "result_revealed_source_event_id"
            ],
        )
