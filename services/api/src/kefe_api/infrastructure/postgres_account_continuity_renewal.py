from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Connection, text

from kefe_api.core.errors import DomainError
from kefe_api.infrastructure.postgres_account_continuity import (
    PostgresAccountContinuityRepository,
)
from kefe_api.infrastructure.postgres_otp_request_guard import (
    GuardedPostgresAccountContinuityRepository,
)
from kefe_api.modules.identity.account_models import GuestMergeReplay
from kefe_api.modules.identity.account_ports import AccountSessionMaterialFactory


class _RenewalAccountMergeMixin:
    def complete_guest_merge(
        self,
        *,
        source_actor_id: UUID,
        verification_token_hash: str,
        account_token_hash: str,
        account_session_expires_at: datetime,
        completed_at: datetime,
        session_material_factory: AccountSessionMaterialFactory | None = None,
    ) -> GuestMergeReplay:
        with self._engine.begin() as connection:
            existing = self._replay(
                self._select_guest_merge_replay(connection, verification_token_hash)
            )
            if existing is not None:
                self._require_matching_source(existing, source_actor_id)
                return existing

            verification_row = connection.execute(
                text(
                    """
                    UPDATE identity.otp_verification
                    SET consumed_at = :completed_at
                    WHERE token_hash = :verification_token_hash
                      AND consumed_at IS NULL
                      AND expires_at > :completed_at
                    RETURNING token_hash, identifier_hash, channel, identifier_hint,
                              verified_at, expires_at
                    """
                ),
                {
                    "verification_token_hash": verification_token_hash,
                    "completed_at": completed_at,
                },
            ).mappings().one_or_none()
            if verification_row is None:
                existing = self._replay(
                    self._select_guest_merge_replay(connection, verification_token_hash)
                )
                if existing is not None:
                    self._require_matching_source(existing, source_actor_id)
                    return existing
                raise DomainError(
                    "AUTH_VERIFICATION_INVALID",
                    "Verification token is invalid or expired",
                    401,
                )

            verification = self._verification(verification_row)
            if verification is None:
                raise DomainError(
                    "AUTH_VERIFICATION_INVALID",
                    "Verification token is invalid or expired",
                    401,
                )
            account_actor_id, merged_from_actor_id = self._upgrade_or_merge_guest(
                connection,
                guest_actor_id=source_actor_id,
                identifier_hash=verification.identifier_hash,
                channel=verification.channel,
                identifier_hint=verification.identifier_hint,
                verified_at=verification.verified_at,
            )

            material = (
                session_material_factory(actor_id=account_actor_id, now=completed_at)
                if session_material_factory is not None
                else None
            )
            if material is None:
                session_id = None
                session_expires_at = account_session_expires_at
                connection.execute(
                    text(
                        """
                        INSERT INTO identity.actor_session (id, actor_id, token_hash, expires_at)
                        VALUES (gen_random_uuid(), :actor_id, :token_hash, :expires_at)
                        """
                    ),
                    {
                        "actor_id": account_actor_id,
                        "token_hash": account_token_hash,
                        "expires_at": account_session_expires_at,
                    },
                )
            else:
                session_id = material.session_id
                session_expires_at = material.access_expires_at
                connection.execute(
                    text(
                        """
                        INSERT INTO identity.actor_session (
                            id, actor_id, token_hash, expires_at,
                            renewal_token_hash, rotation_counter,
                            token_derivation_key_id,
                            continuity_absolute_expires_at,
                            continuity_inactive_expires_at
                        ) VALUES (
                            :id, :actor_id, :token_hash, :expires_at,
                            :renewal_token_hash, :rotation_counter,
                            :token_derivation_key_id,
                            :continuity_absolute_expires_at,
                            :continuity_inactive_expires_at
                        )
                        """
                    ),
                    {
                        "id": material.session_id,
                        "actor_id": account_actor_id,
                        "token_hash": material.access_token_hash,
                        "expires_at": material.access_expires_at,
                        "renewal_token_hash": material.renewal_token_hash,
                        "rotation_counter": material.rotation_counter,
                        "token_derivation_key_id": material.derivation_key_id,
                        "continuity_absolute_expires_at": (
                            material.continuity_absolute_expires_at
                        ),
                        "continuity_inactive_expires_at": (
                            material.continuity_inactive_expires_at
                        ),
                    },
                )

            connection.execute(
                text(
                    """
                    INSERT INTO identity.guest_merge_replay (
                        verification_token_hash,
                        source_actor_id,
                        account_actor_id,
                        merged_from_actor_id,
                        account_session_expires_at,
                        completed_at,
                        account_session_id,
                        account_session_rotation_counter,
                        account_session_derivation_key_id,
                        continuity_absolute_expires_at,
                        continuity_inactive_expires_at
                    ) VALUES (
                        :verification_token_hash,
                        :source_actor_id,
                        :account_actor_id,
                        :merged_from_actor_id,
                        :account_session_expires_at,
                        :completed_at,
                        :account_session_id,
                        :account_session_rotation_counter,
                        :account_session_derivation_key_id,
                        :continuity_absolute_expires_at,
                        :continuity_inactive_expires_at
                    )
                    """
                ),
                {
                    "verification_token_hash": verification_token_hash,
                    "source_actor_id": source_actor_id,
                    "account_actor_id": account_actor_id,
                    "merged_from_actor_id": merged_from_actor_id,
                    "account_session_expires_at": session_expires_at,
                    "completed_at": completed_at,
                    "account_session_id": session_id,
                    "account_session_rotation_counter": (
                        material.rotation_counter if material is not None else None
                    ),
                    "account_session_derivation_key_id": (
                        material.derivation_key_id if material is not None else None
                    ),
                    "continuity_absolute_expires_at": (
                        material.continuity_absolute_expires_at
                        if material is not None
                        else None
                    ),
                    "continuity_inactive_expires_at": (
                        material.continuity_inactive_expires_at
                        if material is not None
                        else None
                    ),
                },
            )
            return GuestMergeReplay(
                verification_token_hash=verification_token_hash,
                source_actor_id=source_actor_id,
                account_actor_id=account_actor_id,
                merged_from_actor_id=merged_from_actor_id,
                account_session_expires_at=session_expires_at,
                completed_at=completed_at,
                account_session_id=session_id,
                account_session_rotation_counter=(
                    material.rotation_counter if material is not None else 0
                ),
                account_session_derivation_key_id=(
                    material.derivation_key_id if material is not None else None
                ),
                continuity_absolute_expires_at=(
                    material.continuity_absolute_expires_at if material is not None else None
                ),
                continuity_inactive_expires_at=(
                    material.continuity_inactive_expires_at if material is not None else None
                ),
            )

    @staticmethod
    def _select_guest_merge_replay(
        connection: Connection,
        verification_token_hash: str,
    ):
        return connection.execute(
            text(
                """
                SELECT verification_token_hash,
                       source_actor_id,
                       account_actor_id,
                       merged_from_actor_id,
                       account_session_expires_at,
                       completed_at,
                       account_session_id,
                       account_session_rotation_counter,
                       account_session_derivation_key_id,
                       continuity_absolute_expires_at,
                       continuity_inactive_expires_at
                FROM identity.guest_merge_replay
                WHERE verification_token_hash = :verification_token_hash
                """
            ),
            {"verification_token_hash": verification_token_hash},
        ).mappings().one_or_none()

    @staticmethod
    def _replay(row) -> GuestMergeReplay | None:
        if row is None:
            return None
        return GuestMergeReplay(
            verification_token_hash=row["verification_token_hash"],
            source_actor_id=row["source_actor_id"],
            account_actor_id=row["account_actor_id"],
            merged_from_actor_id=row["merged_from_actor_id"],
            account_session_expires_at=row["account_session_expires_at"],
            completed_at=row["completed_at"],
            account_session_id=row["account_session_id"],
            account_session_rotation_counter=(
                row["account_session_rotation_counter"] or 0
            ),
            account_session_derivation_key_id=(
                row["account_session_derivation_key_id"]
            ),
            continuity_absolute_expires_at=row["continuity_absolute_expires_at"],
            continuity_inactive_expires_at=row["continuity_inactive_expires_at"],
        )


class RenewalPostgresAccountContinuityRepository(
    _RenewalAccountMergeMixin,
    PostgresAccountContinuityRepository,
):
    pass


class GuardedRenewalPostgresAccountContinuityRepository(
    _RenewalAccountMergeMixin,
    GuardedPostgresAccountContinuityRepository,
):
    pass
