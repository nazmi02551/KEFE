from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Engine, text

from kefe_api.modules.events.models import OutboxEvent


class PostgresOutboxStore:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def claim_batch(
        self,
        *,
        worker_id: str,
        limit: int,
        lease_seconds: int,
    ) -> list[OutboxEvent]:
        with self._engine.begin() as connection:
            rows = connection.execute(
                text(
                    """
                    WITH candidates AS (
                        SELECT id
                        FROM analytics.outbox_event
                        WHERE published_at IS NULL
                          AND dead_lettered_at IS NULL
                          AND next_attempt_at <= now()
                          AND (locked_until IS NULL OR locked_until < now())
                        ORDER BY created_at, id
                        FOR UPDATE SKIP LOCKED
                        LIMIT :limit
                    )
                    UPDATE analytics.outbox_event AS event
                    SET
                        lock_owner = :worker_id,
                        locked_until = now() + (:lease_seconds * interval '1 second'),
                        attempts = event.attempts + 1
                    FROM candidates
                    WHERE event.id = candidates.id
                    RETURNING
                        event.id,
                        event.aggregate_type,
                        event.aggregate_id,
                        event.event_name,
                        event.event_version,
                        event.occurred_at,
                        event.payload,
                        event.attempts
                    """
                ),
                {
                    "worker_id": worker_id,
                    "limit": limit,
                    "lease_seconds": lease_seconds,
                },
            ).mappings().all()

        return [
            OutboxEvent(
                id=row["id"],
                aggregate_type=row["aggregate_type"],
                aggregate_id=row["aggregate_id"],
                event_name=row["event_name"],
                event_version=row["event_version"],
                occurred_at=row["occurred_at"],
                payload=row["payload"],
                attempts=row["attempts"],
            )
            for row in rows
        ]

    def mark_published(self, *, event_id: UUID, worker_id: str) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE analytics.outbox_event
                    SET
                        published_at = now(),
                        lock_owner = NULL,
                        locked_until = NULL,
                        last_error = NULL
                    WHERE id = :event_id
                      AND lock_owner = :worker_id
                      AND published_at IS NULL
                    """
                ),
                {"event_id": event_id, "worker_id": worker_id},
            )

    def mark_failed(
        self,
        *,
        event_id: UUID,
        worker_id: str,
        error: str,
        next_attempt_at: datetime,
        dead_letter: bool,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE analytics.outbox_event
                    SET
                        next_attempt_at = :next_attempt_at,
                        last_error = :error,
                        dead_lettered_at = CASE
                            WHEN :dead_letter THEN now()
                            ELSE dead_lettered_at
                        END,
                        lock_owner = NULL,
                        locked_until = NULL
                    WHERE id = :event_id
                      AND lock_owner = :worker_id
                      AND published_at IS NULL
                    """
                ),
                {
                    "event_id": event_id,
                    "worker_id": worker_id,
                    "error": error,
                    "next_attempt_at": next_attempt_at,
                    "dead_letter": dead_letter,
                },
            )
