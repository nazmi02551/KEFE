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


class PostgresIdentityRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_guest_session(
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
                        expires_at
                    )
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

    def resolve_token(self, *, token_hash: str, now: datetime) -> TokenResolution:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT
                        actor.id AS actor_id,
                        actor.actor_kind,
                        actor.state,
                        session.expires_at,
                        session.revoked_at
                    FROM identity.actor_session AS session
                    JOIN identity.actor AS actor ON actor.id = session.actor_id
                    WHERE session.token_hash = :token_hash
                    LIMIT 1
                    """
                ),
                {"token_hash": token_hash},
            ).mappings().one_or_none()

        if row is None:
            return TokenResolution(TokenStatus.INVALID)
        # Session lifecycle is more specific than actor lifecycle. Preserve an explicit
        # revoked classification even when a merge has retired the source guest actor.
        if row["revoked_at"] is not None:
            return TokenResolution(TokenStatus.REVOKED)
        if row["state"] != "ACTIVE":
            return TokenResolution(TokenStatus.INVALID)
        if row["expires_at"] <= now:
            return TokenResolution(TokenStatus.EXPIRED)
        return TokenResolution(
            TokenStatus.ACTIVE,
            ActorPrincipal(
                actor_id=row["actor_id"],
                actor_kind=ActorKind(row["actor_kind"]),
            ),
        )

    def revoke_token(self, *, token_hash: str, now: datetime) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    UPDATE identity.actor_session
                    SET revoked_at = COALESCE(revoked_at, :now)
                    WHERE token_hash = :token_hash
                    """
                ),
                {"token_hash": token_hash, "now": now},
            )
