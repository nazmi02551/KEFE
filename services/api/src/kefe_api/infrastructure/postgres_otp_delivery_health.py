from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import Engine, text

from kefe_api.modules.identity.otp_delivery_health import (
    OtpDeliveryAlertAcknowledgement,
    OtpDeliveryAlertCandidate,
    OtpDeliveryAlertPolicy,
    OtpDeliveryAlertRecord,
    OtpDeliveryHealthEvent,
    OtpDeliveryHealthFacts,
    OtpDeliveryHealthPolicy,
    OtpDeliveryHealthSignal,
    _snapshot_from_facts,
)

_ALERT_ADVISORY_LOCK = 4_604_954_681


class PostgresOtpDeliveryHealthRepository:
    def __init__(
        self,
        engine: Engine,
        *,
        health_policy: OtpDeliveryHealthPolicy | None = None,
        alert_policy: OtpDeliveryAlertPolicy | None = None,
    ) -> None:
        self._engine = engine
        self._health_policy = health_policy or OtpDeliveryHealthPolicy()
        self._alert_policy = alert_policy or OtpDeliveryAlertPolicy()

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

        # Concurrent delivery completions may commit out of observed-time order.
        # Evaluate against the newest durable event so escalation cannot be missed.
        with self._engine.connect() as connection:
            latest_observed_at = connection.execute(
                text("SELECT max(observed_at) FROM identity.otp_delivery_event")
            ).scalar_one()
        evaluation_as_of = latest_observed_at or event.observed_at
        facts = self.read_facts(
            window_started_at=evaluation_as_of - self._health_policy.window,
            as_of=evaluation_as_of,
            prune_before=evaluation_as_of - self._health_policy.retention,
        )
        snapshot = _snapshot_from_facts(facts, self._health_policy)
        if snapshot.signal in (
            OtpDeliveryHealthSignal.ATTENTION,
            OtpDeliveryHealthSignal.CRITICAL,
        ):
            self._create_alert_candidate_if_due(
                OtpDeliveryAlertCandidate.from_snapshot(snapshot)
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

    def list_alert_candidates(
        self,
        *,
        acknowledged: bool | None,
        limit: int,
        offset: int,
        as_of: datetime,
    ) -> tuple[OtpDeliveryAlertRecord, ...]:
        if not 1 <= limit <= 100:
            raise ValueError("OTP delivery alert limit is outside the supported range")
        if not 0 <= offset <= 10_000:
            raise ValueError("OTP delivery alert offset is outside the supported range")
        with self._engine.begin() as connection:
            self._prune_alerts(connection, as_of=as_of)
            rows = connection.execute(
                text(
                    """
                    SELECT
                        c.id,
                        c.signal,
                        c.reason_codes,
                        c.observed_at,
                        c.window_started_at,
                        c.total_count,
                        c.accepted_count,
                        c.unavailable_count,
                        c.rejected_count,
                        c.failure_ratio_bps,
                        c.created_at,
                        a.acknowledged_at,
                        a.actor_ref,
                        a.created_at AS acknowledgement_created_at
                    FROM identity.otp_delivery_alert_candidate AS c
                    LEFT JOIN identity.otp_delivery_alert_acknowledgement AS a
                      ON a.candidate_id = c.id
                    WHERE (
                        CAST(:acknowledged AS boolean) IS NULL
                        OR (a.candidate_id IS NOT NULL) = CAST(:acknowledged AS boolean)
                    )
                    ORDER BY c.observed_at DESC, c.id DESC
                    LIMIT :limit OFFSET :offset
                    """
                ),
                {
                    "acknowledged": acknowledged,
                    "limit": limit,
                    "offset": offset,
                },
            ).mappings().all()
        return tuple(_alert_record_from_row(row) for row in rows)

    def acknowledge_alert(
        self,
        acknowledgement: OtpDeliveryAlertAcknowledgement,
        *,
        as_of: datetime,
    ) -> OtpDeliveryAlertRecord | None:
        with self._engine.begin() as connection:
            self._prune_alerts(connection, as_of=as_of)
            connection.execute(
                text("SELECT pg_advisory_xact_lock(:lock_key)"),
                {"lock_key": _ALERT_ADVISORY_LOCK},
            )
            exists = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM identity.otp_delivery_alert_candidate
                    WHERE id = :candidate_id
                    """
                ),
                {"candidate_id": acknowledgement.candidate_id},
            ).first()
            if exists is None:
                return None
            connection.execute(
                text(
                    """
                    INSERT INTO identity.otp_delivery_alert_acknowledgement (
                        candidate_id,
                        acknowledged_at,
                        actor_ref,
                        created_at
                    ) VALUES (
                        :candidate_id,
                        :acknowledged_at,
                        :actor_ref,
                        :created_at
                    )
                    ON CONFLICT (candidate_id) DO NOTHING
                    """
                ),
                {
                    "candidate_id": acknowledgement.candidate_id,
                    "acknowledged_at": acknowledgement.acknowledged_at,
                    "actor_ref": acknowledgement.actor_ref,
                    "created_at": acknowledgement.created_at,
                },
            )
            row = connection.execute(
                text(
                    """
                    SELECT
                        c.id,
                        c.signal,
                        c.reason_codes,
                        c.observed_at,
                        c.window_started_at,
                        c.total_count,
                        c.accepted_count,
                        c.unavailable_count,
                        c.rejected_count,
                        c.failure_ratio_bps,
                        c.created_at,
                        a.acknowledged_at,
                        a.actor_ref,
                        a.created_at AS acknowledgement_created_at
                    FROM identity.otp_delivery_alert_candidate AS c
                    LEFT JOIN identity.otp_delivery_alert_acknowledgement AS a
                      ON a.candidate_id = c.id
                    WHERE c.id = :candidate_id
                    """
                ),
                {"candidate_id": acknowledgement.candidate_id},
            ).mappings().one()
        return _alert_record_from_row(row)

    def _create_alert_candidate_if_due(
        self,
        candidate: OtpDeliveryAlertCandidate,
    ) -> bool:
        cooldown_started_at = candidate.observed_at - self._alert_policy.cooldown
        with self._engine.begin() as connection:
            self._prune_alerts(connection, as_of=candidate.observed_at)
            connection.execute(
                text("SELECT pg_advisory_xact_lock(:lock_key)"),
                {"lock_key": _ALERT_ADVISORY_LOCK},
            )
            recent = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM identity.otp_delivery_alert_candidate
                    WHERE observed_at >= :cooldown_started_at
                      AND (
                          signal = :signal
                          OR (:signal = 'ATTENTION' AND signal = 'CRITICAL')
                      )
                    LIMIT 1
                    """
                ),
                {
                    "cooldown_started_at": cooldown_started_at,
                    "signal": candidate.signal.value,
                },
            ).first()
            if recent is not None:
                return False
            connection.execute(
                text(
                    """
                    INSERT INTO identity.otp_delivery_alert_candidate (
                        id,
                        signal,
                        reason_codes,
                        observed_at,
                        window_started_at,
                        total_count,
                        accepted_count,
                        unavailable_count,
                        rejected_count,
                        failure_ratio_bps,
                        created_at
                    ) VALUES (
                        :id,
                        :signal,
                        CAST(:reason_codes AS jsonb),
                        :observed_at,
                        :window_started_at,
                        :total_count,
                        :accepted_count,
                        :unavailable_count,
                        :rejected_count,
                        :failure_ratio_bps,
                        :created_at
                    )
                    """
                ),
                {
                    "id": candidate.id,
                    "signal": candidate.signal.value,
                    "reason_codes": json.dumps(list(candidate.reason_codes)),
                    "observed_at": candidate.observed_at,
                    "window_started_at": candidate.window_started_at,
                    "total_count": candidate.total_count,
                    "accepted_count": candidate.accepted_count,
                    "unavailable_count": candidate.unavailable_count,
                    "rejected_count": candidate.rejected_count,
                    "failure_ratio_bps": candidate.failure_ratio_bps,
                    "created_at": candidate.created_at,
                },
            )
        return True

    def _prune_alerts(self, connection, *, as_of: datetime) -> None:
        connection.execute(
            text(
                """
                DELETE FROM identity.otp_delivery_alert_candidate
                WHERE observed_at < :prune_before
                """
            ),
            {"prune_before": as_of - self._alert_policy.retention},
        )


def _alert_record_from_row(row) -> OtpDeliveryAlertRecord:
    candidate = OtpDeliveryAlertCandidate(
        id=row["id"],
        signal=OtpDeliveryHealthSignal(row["signal"]),
        reason_codes=tuple(sorted(str(item) for item in row["reason_codes"])),
        observed_at=row["observed_at"],
        window_started_at=row["window_started_at"],
        total_count=int(row["total_count"]),
        accepted_count=int(row["accepted_count"]),
        unavailable_count=int(row["unavailable_count"]),
        rejected_count=int(row["rejected_count"]),
        failure_ratio_bps=(
            int(row["failure_ratio_bps"])
            if row["failure_ratio_bps"] is not None
            else None
        ),
        created_at=row["created_at"],
    )
    acknowledgement = None
    if row["acknowledged_at"] is not None:
        acknowledgement = OtpDeliveryAlertAcknowledgement(
            candidate_id=candidate.id,
            acknowledged_at=row["acknowledged_at"],
            actor_ref=str(row["actor_ref"]),
            created_at=row["acknowledgement_created_at"],
        )
    return OtpDeliveryAlertRecord(
        candidate=candidate,
        acknowledgement=acknowledgement,
    )
