from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Engine, text

from kefe_api.modules.identity.models import (
    ActorKind,
    ActorPrincipal,
    TokenResolution,
    TokenStatus,
)
from kefe_api.modules.identity.session_renewal import (
    RenewalResolution,
    RenewalResolutionStatus,
    RenewalTokenMatch,
    SessionRenewalSnapshot,
    SessionRotationMutation,
)


class PostgresIdentityRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_guest_session(
        self,
        *,
        actor_id: UUID,
        token_hash: str,
        expires_at: datetime,
        session_id: UUID | None = None,
        renewal_token_hash: str | None = None,
        rotation_counter: int = 0,
        token_derivation_key_id: str | None = None,
        continuity_absolute_expires_at: datetime | None = None,
        continuity_inactive_expires_at: datetime | None = None,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO identity.actor (id, actor_kind, state)
                    VALUES (:actor_id, 'GUEST', 'ACTIVE')
                    """
                ),
                {"actor_id": actor_id},
            )
            connection.execute(
                text(
                    """
                    INSERT INTO identity.actor_session (
                        id,
                        actor_id,
                        token_hash,
                        expires_at,
                        renewal_token_hash,
                        rotation_counter,
                        token_derivation_key_id,
                        continuity_absolute_expires_at,
                        continuity_inactive_expires_at
                    )
                    VALUES (
                        :id,
                        :actor_id,
                        :token_hash,
                        :expires_at,
                        :renewal_token_hash,
                        :rotation_counter,
                        :token_derivation_key_id,
                        :continuity_absolute_expires_at,
                        :continuity_inactive_expires_at
                    )
                    """
                ),
                {
                    "id": session_id or uuid4(),
                    "actor_id": actor_id,
                    "token_hash": token_hash,
                    "expires_at": expires_at,
                    "renewal_token_hash": renewal_token_hash,
                    "rotation_counter": rotation_counter,
                    "token_derivation_key_id": token_derivation_key_id,
                    "continuity_absolute_expires_at": continuity_absolute_expires_at,
                    "continuity_inactive_expires_at": continuity_inactive_expires_at,
                },
            )

    def resolve_token(self, *, token_hash: str, now: datetime) -> TokenResolution:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        actor.id AS actor_id,
                        actor.actor_kind,
                        actor.state,
                        session.token_hash,
                        session.expires_at,
                        session.revoked_at
                    FROM identity.actor_session AS session
                    JOIN identity.actor AS actor ON actor.id = session.actor_id
                    WHERE
                        session.token_hash = :token_hash
                        OR (
                            session.previous_token_hash = :token_hash
                            AND session.previous_token_valid_until IS NOT NULL
                            AND session.previous_token_valid_until >= :now
                        )
                    LIMIT 1
                    """
                ),
                {"token_hash": token_hash, "now": now},
            ).mappings().one_or_none()

        if row is None:
            return TokenResolution(TokenStatus.INVALID)
        if row["revoked_at"] is not None:
            return TokenResolution(
                TokenStatus.REVOKED,
                ActorPrincipal(
                    actor_id=row["actor_id"],
                    actor_kind=ActorKind(row["actor_kind"]),
                ),
            )
        if row["state"] != "ACTIVE":
            return TokenResolution(TokenStatus.INVALID)
        if row["token_hash"] == token_hash and row["expires_at"] <= now:
            return TokenResolution(TokenStatus.EXPIRED)
        return TokenResolution(
            TokenStatus.ACTIVE,
            ActorPrincipal(
                actor_id=row["actor_id"],
                actor_kind=ActorKind(row["actor_kind"]),
            ),
        )

    def resolve_renewal(
        self,
        *,
        renewal_token_hash: str,
        now: datetime,
    ) -> RenewalResolution:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        session.id AS session_id,
                        actor.id AS actor_id,
                        actor.actor_kind,
                        actor.state,
                        session.token_hash,
                        session.renewal_token_hash,
                        session.rotation_counter,
                        session.token_derivation_key_id,
                        session.expires_at,
                        session.revoked_at,
                        session.continuity_absolute_expires_at,
                        session.continuity_inactive_expires_at,
                        CASE
                            WHEN session.renewal_token_hash = :renewal_token_hash
                                THEN 'CURRENT'
                            ELSE 'PREVIOUS_GRACE'
                        END AS token_match
                    FROM identity.actor_session AS session
                    JOIN identity.actor AS actor ON actor.id = session.actor_id
                    WHERE
                        session.renewal_token_hash = :renewal_token_hash
                        OR (
                            session.previous_renewal_token_hash = :renewal_token_hash
                            AND session.previous_renewal_valid_until IS NOT NULL
                            AND session.previous_renewal_valid_until >= :now
                        )
                    LIMIT 1
                    """
                ),
                {"renewal_token_hash": renewal_token_hash, "now": now},
            ).mappings().one_or_none()

        if row is None:
            return RenewalResolution(RenewalResolutionStatus.INVALID)
        if row["revoked_at"] is not None:
            return RenewalResolution(RenewalResolutionStatus.REVOKED)
        if row["state"] != "ACTIVE":
            return RenewalResolution(RenewalResolutionStatus.INVALID)
        if (
            row["token_derivation_key_id"] is None
            or row["renewal_token_hash"] is None
            or row["continuity_absolute_expires_at"] is None
            or row["continuity_inactive_expires_at"] is None
        ):
            return RenewalResolution(RenewalResolutionStatus.INVALID)
        if (
            now >= row["continuity_absolute_expires_at"]
            or now >= row["continuity_inactive_expires_at"]
        ):
            return RenewalResolution(RenewalResolutionStatus.CONTINUITY_EXPIRED)

        return RenewalResolution(
            RenewalResolutionStatus.ACTIVE,
            SessionRenewalSnapshot(
                session_id=row["session_id"],
                actor_id=row["actor_id"],
                actor_kind=ActorKind(row["actor_kind"]),
                rotation_counter=row["rotation_counter"],
                derivation_key_id=row["token_derivation_key_id"],
                access_token_hash=row["token_hash"],
                renewal_token_hash=row["renewal_token_hash"],
                access_expires_at=row["expires_at"],
                continuity_absolute_expires_at=row["continuity_absolute_expires_at"],
                continuity_inactive_expires_at=row["continuity_inactive_expires_at"],
                token_match=RenewalTokenMatch(row["token_match"]),
            ),
        )

    def rotate_session(self, *, mutation: SessionRotationMutation) -> bool:
        with self._engine.begin() as connection:
            row = connection.execute(
                text(
                    """
                    UPDATE identity.actor_session
                    SET
                        previous_token_hash = token_hash,
                        previous_token_valid_until = LEAST(
                            :previous_pair_valid_until,
                            expires_at
                        ),
                        previous_renewal_token_hash = renewal_token_hash,
                        previous_renewal_valid_until = :previous_pair_valid_until,
                        token_hash = :next_access_token_hash,
                        renewal_token_hash = :next_renewal_token_hash,
                        expires_at = :next_access_expires_at,
                        continuity_inactive_expires_at = LEAST(
                            :next_inactive_expires_at,
                            continuity_absolute_expires_at
                        ),
                        rotation_counter = :next_rotation_counter,
                        token_derivation_key_id = :next_derivation_key_id,
                        renewed_at = :renewed_at
                    WHERE
                        id = :session_id
                        AND revoked_at IS NULL
                        AND rotation_counter = :expected_rotation_counter
                        AND token_hash = :current_access_token_hash
                        AND renewal_token_hash = :current_renewal_token_hash
                        AND continuity_absolute_expires_at > :renewed_at
                        AND continuity_inactive_expires_at > :renewed_at
                    RETURNING id
                    """
                ),
                {
                    "session_id": mutation.session_id,
                    "expected_rotation_counter": mutation.expected_rotation_counter,
                    "current_access_token_hash": mutation.current_access_token_hash,
                    "current_renewal_token_hash": mutation.current_renewal_token_hash,
                    "next_access_token_hash": mutation.next_access_token_hash,
                    "next_renewal_token_hash": mutation.next_renewal_token_hash,
                    "next_access_expires_at": mutation.next_access_expires_at,
                    "next_inactive_expires_at": mutation.next_inactive_expires_at,
                    "next_rotation_counter": mutation.next_rotation_counter,
                    "next_derivation_key_id": mutation.next_derivation_key_id,
                    "previous_pair_valid_until": mutation.previous_pair_valid_until,
                    "renewed_at": mutation.renewed_at,
                },
            ).first()
        return row is not None

    def revoke_token(self, *, token_hash: str, now: datetime) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE identity.actor_session
                    SET revoked_at = COALESCE(revoked_at, :now)
                    WHERE
                        token_hash = :token_hash
                        OR (
                            previous_token_hash = :token_hash
                            AND previous_token_valid_until IS NOT NULL
                            AND previous_token_valid_until >= :now
                        )
                    """
                ),
                {"token_hash": token_hash, "now": now},
            )
