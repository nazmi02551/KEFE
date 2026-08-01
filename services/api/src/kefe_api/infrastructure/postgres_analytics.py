from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.analytics.models import (
    AnalyticsEvent,
    AnalyticsPrivacyClass,
    AnalyticsRetentionClass,
)


class PostgresAnalyticsEventStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def append_once(self, event: AnalyticsEvent) -> bool:
        with self._engine.begin() as connection:
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
