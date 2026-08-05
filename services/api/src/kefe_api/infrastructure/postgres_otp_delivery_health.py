from __future__ import annotations

from datetime import datetime

from sqlalchemy import Engine, text

from kefe_api.modules.identity.otp_delivery_health import (
    OtpDeliveryHealthEvent,
    OtpDeliveryHealthFacts,
)


class PostgresOtpDeliveryHealthRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def append_and_prune(
        self,
        event: OtpDeliveryHealthEvent,
        *,
        prune_before: datetime,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM identity.otp_delivery_event
                    WHERE observed_at < :prune_before
                    """
                ),
                {"prune_before": prune_before},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO identity.otp_delivery_event (
                        id,
                        observed_at,
                        channel,
                        outcome,
                        attempts,
                        status_code,
                        error_code
                    ) VALUES (
                        :id,
                        :observed_at,
                        :channel,
                        :outcome,
                        :attempts,
                        :status_code,
                        :error_code
                    )
                    """
                ),
                {
                    "id": event.id,
                    "observed_at": event.observed_at,
                    "channel": event.channel.value,
                    "outcome": event.outcome.value,
                    "attempts": event.attempts,
                    "status_code": event.status_code,
                    "error_code": event.error_code,
                },
            )

    def read_facts(
        self,
        *,
        window_started_at: datetime,
        as_of: datetime,
        prune_before: datetime,
    ) -> OtpDeliveryHealthFacts:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM identity.otp_delivery_event
                    WHERE observed_at < :prune_before
                    """
                ),
                {"prune_before": prune_before},
            )
            row = connection.execute(
                text(
                    """
                    SELECT
                        count(*)::integer AS total_count,
                        count(*) FILTER (WHERE outcome = 'ACCEPTED')::integer
                            AS accepted_count,
                        count(*) FILTER (WHERE outcome = 'UNAVAILABLE')::integer
                            AS unavailable_count,
                        count(*) FILTER (WHERE outcome = 'REJECTED')::integer
                            AS rejected_count,
                        COALESCE(sum(attempts), 0)::integer AS attempts_total,
                        count(*) FILTER (WHERE channel = 'EMAIL')::integer
                            AS email_count,
                        count(*) FILTER (WHERE channel = 'SMS')::integer
                            AS sms_count,
                        max(observed_at) AS latest_observed_at,
                        max(observed_at) FILTER (WHERE outcome = 'ACCEPTED')
                            AS latest_accepted_at
                    FROM identity.otp_delivery_event
                    WHERE observed_at >= :window_started_at
                      AND observed_at <= :as_of
                    """
                ),
                {
                    "window_started_at": window_started_at,
                    "as_of": as_of,
                },
            ).mappings().one()
        return OtpDeliveryHealthFacts(
            as_of=as_of,
            window_started_at=window_started_at,
            total_count=int(row["total_count"]),
            accepted_count=int(row["accepted_count"]),
            unavailable_count=int(row["unavailable_count"]),
            rejected_count=int(row["rejected_count"]),
            attempts_total=int(row["attempts_total"]),
            email_count=int(row["email_count"]),
            sms_count=int(row["sms_count"]),
            latest_observed_at=row["latest_observed_at"],
            latest_accepted_at=row["latest_accepted_at"],
        )
