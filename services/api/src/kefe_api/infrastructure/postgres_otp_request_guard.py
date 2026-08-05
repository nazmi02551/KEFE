from __future__ import annotations

from sqlalchemy import Engine, text

from kefe_api.infrastructure.postgres_account_continuity import (
    PostgresAccountContinuityRepository,
)
from kefe_api.modules.identity.account_models import OtpChallenge
from kefe_api.modules.identity.otp_request_guard import (
    OtpRequestAbusePolicy,
    otp_request_rate_limited_error,
)


class GuardedPostgresAccountContinuityRepository(
    PostgresAccountContinuityRepository
):
    def __init__(self, engine: Engine, policy: OtpRequestAbusePolicy) -> None:
        super().__init__(engine)
        self._otp_request_policy = policy

    def create_challenge(self, challenge: OtpChallenge) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    DELETE FROM identity.otp_request_guard
                    WHERE retention_expires_at <= :requested_at
                    """
                ),
                {"requested_at": challenge.requested_at},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO identity.otp_challenge (
                        id, channel, identifier_hash, identifier_hint, code_hash,
                        requested_at, expires_at, consumed_at, failed_attempts
                    ) VALUES (
                        :id, :channel, :identifier_hash, :identifier_hint, :code_hash,
                        :requested_at, :expires_at, :consumed_at, :failed_attempts
                    )
                    """
                ),
                {
                    "id": challenge.id,
                    "channel": challenge.channel.value,
                    "identifier_hash": challenge.identifier_hash,
                    "identifier_hint": challenge.identifier_hint,
                    "code_hash": challenge.code_hash,
                    "requested_at": challenge.requested_at,
                    "expires_at": challenge.expires_at,
                    "consumed_at": challenge.consumed_at,
                    "failed_attempts": challenge.failed_attempts,
                },
            )
            inserted = connection.execute(
                text(
                    """
                    INSERT INTO identity.otp_request_guard (
                        channel,
                        identifier_hash,
                        latest_challenge_id,
                        window_started_at,
                        last_requested_at,
                        request_count,
                        retention_expires_at,
                        updated_at
                    ) VALUES (
                        :channel,
                        :identifier_hash,
                        :latest_challenge_id,
                        :requested_at,
                        :requested_at,
                        1,
                        :retention_expires_at,
                        :requested_at
                    )
                    ON CONFLICT (channel, identifier_hash) DO NOTHING
                    RETURNING identifier_hash
                    """
                ),
                {
                    "channel": challenge.channel.value,
                    "identifier_hash": challenge.identifier_hash,
                    "latest_challenge_id": challenge.id,
                    "requested_at": challenge.requested_at,
                    "retention_expires_at": (
                        challenge.requested_at + self._otp_request_policy.retention
                    ),
                },
            ).scalar_one_or_none()
            if inserted is not None:
                return

            row = connection.execute(
                text(
                    """
                    SELECT window_started_at,
                           last_requested_at,
                           request_count
                    FROM identity.otp_request_guard
                    WHERE channel = :channel
                      AND identifier_hash = :identifier_hash
                    FOR UPDATE
                    """
                ),
                {
                    "channel": challenge.channel.value,
                    "identifier_hash": challenge.identifier_hash,
                },
            ).mappings().one()

            if (
                challenge.requested_at
                < row["last_requested_at"] + self._otp_request_policy.cooldown
            ):
                raise otp_request_rate_limited_error()

            if (
                challenge.requested_at
                >= row["window_started_at"] + self._otp_request_policy.window
            ):
                window_started_at = challenge.requested_at
                request_count = 0
            else:
                window_started_at = row["window_started_at"]
                request_count = int(row["request_count"])

            if request_count >= self._otp_request_policy.window_limit:
                raise otp_request_rate_limited_error()

            connection.execute(
                text(
                    """
                    UPDATE identity.otp_request_guard
                    SET latest_challenge_id = :latest_challenge_id,
                        window_started_at = :window_started_at,
                        last_requested_at = :requested_at,
                        request_count = :request_count,
                        retention_expires_at = :retention_expires_at,
                        updated_at = :requested_at
                    WHERE channel = :channel
                      AND identifier_hash = :identifier_hash
                    """
                ),
                {
                    "latest_challenge_id": challenge.id,
                    "window_started_at": window_started_at,
                    "requested_at": challenge.requested_at,
                    "request_count": request_count + 1,
                    "retention_expires_at": (
                        challenge.requested_at + self._otp_request_policy.retention
                    ),
                    "channel": challenge.channel.value,
                    "identifier_hash": challenge.identifier_hash,
                },
            )
