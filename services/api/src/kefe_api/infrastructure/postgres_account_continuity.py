from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Engine, text

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.account_models import (
    AccountIdentity,
    OtpChallenge,
    OtpChannel,
    OtpVerification,
)


class PostgresAccountContinuityRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_challenge(self, challenge: OtpChallenge) -> None:
        with self._engine.begin() as connection:
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

    def get_challenge(self, challenge_id: UUID) -> OtpChallenge | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT id, channel, identifier_hash, identifier_hint, code_hash,
                           requested_at, expires_at, consumed_at, failed_attempts
                    FROM identity.otp_challenge
                    WHERE id = :id
                    """
                ),
                {"id": challenge_id},
            ).mappings().one_or_none()
        if row is None:
            return None
        return OtpChallenge(
            id=row["id"],
            channel=OtpChannel(row["channel"]),
            identifier_hash=row["identifier_hash"],
            identifier_hint=row["identifier_hint"],
            code_hash=row["code_hash"],
            requested_at=row["requested_at"],
            expires_at=row["expires_at"],
            consumed_at=row["consumed_at"],
            failed_attempts=row["failed_attempts"],
        )

    def record_failed_attempt(self, challenge_id: UUID) -> int:
        with self._engine.begin() as connection:
            value = connection.execute(
                text(
                    """
                    UPDATE identity.otp_challenge
                    SET failed_attempts = failed_attempts + 1
                    WHERE id = :id AND consumed_at IS NULL
                    RETURNING failed_attempts
                    """
                ),
                {"id": challenge_id},
            ).scalar_one_or_none()
        return int(value or 0)

    def consume_challenge(
        self,
        *,
        challenge_id: UUID,
        consumed_at: datetime,
        verification: OtpVerification,
    ) -> bool:
        with self._engine.begin() as connection:
            consumed = connection.execute(
                text(
                    """
                    UPDATE identity.otp_challenge
                    SET consumed_at = :consumed_at
                    WHERE id = :id AND consumed_at IS NULL AND expires_at > :consumed_at
                    RETURNING id
                    """
                ),
                {"id": challenge_id, "consumed_at": consumed_at},
            ).scalar_one_or_none()
            if consumed is None:
                return False
            connection.execute(
                text(
                    """
                    INSERT INTO identity.otp_verification (
                        token_hash, identifier_hash, channel, identifier_hint,
                        verified_at, expires_at, consumed_at
                    ) VALUES (
                        :token_hash, :identifier_hash, :channel, :identifier_hint,
                        :verified_at, :expires_at, NULL
                    )
                    """
                ),
                {
                    "token_hash": verification.token_hash,
                    "identifier_hash": verification.identifier_hash,
                    "channel": verification.channel.value,
                    "identifier_hint": verification.identifier_hint,
                    "verified_at": verification.verified_at,
                    "expires_at": verification.expires_at,
                },
            )
        return True

    def consume_verification(self, *, token_hash: str, now: datetime) -> OtpVerification | None:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE identity.otp_verification
                    SET consumed_at = :now
                    WHERE token_hash = :token_hash
                      AND consumed_at IS NULL
                      AND expires_at > :now
                    RETURNING token_hash, identifier_hash, channel, identifier_hint,
                              verified_at, expires_at
                    """
                ),
                {"token_hash": token_hash, "now": now},
            ).mappings().one_or_none()
        if row is None:
            return None
        return OtpVerification(
            token_hash=row["token_hash"],
            identifier_hash=row["identifier_hash"],
            channel=OtpChannel(row["channel"]),
            identifier_hint=row["identifier_hint"],
            verified_at=row["verified_at"],
            expires_at=row["expires_at"],
        )

    def get_account_by_identifier(self, identifier_hash: str) -> AccountIdentity | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT actor_id, identifier_hash, channel, identifier_hint, verified_at
                    FROM identity.account_identifier
                    WHERE identifier_hash = :identifier_hash
                    """
                ),
                {"identifier_hash": identifier_hash},
            ).mappings().one_or_none()
        if row is None:
            return None
        return AccountIdentity(
            actor_id=row["actor_id"],
            identifier_hash=row["identifier_hash"],
            channel=OtpChannel(row["channel"]),
            identifier_hint=row["identifier_hint"],
            verified_at=row["verified_at"],
        )

    def upgrade_or_merge_guest(
        self,
        *,
        guest_actor_id: UUID,
        identifier_hash: str,
        channel: OtpChannel,
        identifier_hint: str,
        verified_at: datetime,
    ) -> tuple[UUID, UUID | None]:
        with self._engine.begin() as connection:
            guest = connection.execute(
                text("SELECT id, actor_kind, state FROM identity.actor WHERE id = :id FOR UPDATE"),
                {"id": guest_actor_id},
            ).mappings().one_or_none()
            if guest is None or guest["state"] != "ACTIVE" or guest["actor_kind"] != "GUEST":
                raise DomainError("AUTH_GUEST_REQUIRED", "Active guest identity is required", 409)

            existing = connection.execute(
                text(
                    """
                    SELECT actor_id
                    FROM identity.account_identifier
                    WHERE identifier_hash = :identifier_hash
                    FOR UPDATE
                    """
                ),
                {"identifier_hash": identifier_hash},
            ).scalar_one_or_none()

            if existing is None:
                connection.execute(
                    text("UPDATE identity.actor SET actor_kind = 'ACCOUNT' WHERE id = :id"),
                    {"id": guest_actor_id},
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO identity.account_identifier (
                            identifier_hash, actor_id, channel, identifier_hint, verified_at
                        ) VALUES (
                            :identifier_hash, :actor_id, :channel, :identifier_hint, :verified_at
                        )
                        """
                    ),
                    {
                        "identifier_hash": identifier_hash,
                        "actor_id": guest_actor_id,
                        "channel": channel.value,
                        "identifier_hint": identifier_hint,
                        "verified_at": verified_at,
                    },
                )
                return guest_actor_id, None

            account_actor_id = existing
            if account_actor_id == guest_actor_id:
                connection.execute(
                    text("UPDATE identity.actor SET actor_kind = 'ACCOUNT' WHERE id = :id"),
                    {"id": guest_actor_id},
                )
                return guest_actor_id, None

            # Preserve every decision session. Imported sessions are explicitly marked so
            # two historical commits for the same CaseVersion can coexist after merge.
            connection.execute(
                text(
                    """
                    UPDATE decision.weigh_session
                    SET actor_id = :account_actor_id,
                        merged_from_actor_id = COALESCE(merged_from_actor_id, :guest_actor_id)
                    WHERE actor_id = :guest_actor_id
                    """
                ),
                {"account_actor_id": account_actor_id, "guest_actor_id": guest_actor_id},
            )
            for table in (
                "decision.decision_revision",
                "decision.exposure",
                "decision.reflection_completion",
            ):
                connection.execute(
                    text(f"UPDATE {table} SET actor_id = :account_actor_id WHERE actor_id = :guest_actor_id"),
                    {"account_actor_id": account_actor_id, "guest_actor_id": guest_actor_id},
                )

            # Consensus is one participation per account/card-version. Keep the canonical
            # account row if both actors participated; otherwise transfer the guest row.
            connection.execute(
                text(
                    """
                    DELETE FROM collective.consensus_participation guest
                    USING collective.consensus_participation account
                    WHERE guest.actor_id = :guest_actor_id
                      AND account.actor_id = :account_actor_id
                      AND guest.card_version_id = account.card_version_id
                    """
                ),
                {"guest_actor_id": guest_actor_id, "account_actor_id": account_actor_id},
            )
            connection.execute(
                text(
                    """
                    UPDATE collective.consensus_participation
                    SET actor_id = :account_actor_id
                    WHERE actor_id = :guest_actor_id
                    """
                ),
                {"guest_actor_id": guest_actor_id, "account_actor_id": account_actor_id},
            )
            connection.execute(
                text(
                    """
                    UPDATE identity.actor_session
                    SET actor_id = :account_actor_id
                    WHERE actor_id = :guest_actor_id
                    """
                ),
                {"guest_actor_id": guest_actor_id, "account_actor_id": account_actor_id},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO identity.actor_merge (guest_actor_id, account_actor_id, merged_at)
                    VALUES (:guest_actor_id, :account_actor_id, :merged_at)
                    ON CONFLICT (guest_actor_id) DO NOTHING
                    """
                ),
                {
                    "guest_actor_id": guest_actor_id,
                    "account_actor_id": account_actor_id,
                    "merged_at": verified_at,
                },
            )
            connection.execute(
                text("UPDATE identity.actor SET state = 'DELETED' WHERE id = :guest_actor_id"),
                {"guest_actor_id": guest_actor_id},
            )
            return account_actor_id, guest_actor_id

    def create_account_session(
        self,
        *,
        actor_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO identity.actor_session (id, actor_id, token_hash, expires_at)
                    VALUES (:id, :actor_id, :token_hash, :expires_at)
                    """
                ),
                {
                    "id": uuid4(),
                    "actor_id": actor_id,
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                },
            )
