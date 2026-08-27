from __future__ import annotations

from datetime import datetime
from threading import RLock
from uuid import UUID

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.account_models import (
    AccountIdentity,
    GuestMergeReplay,
    OtpChallenge,
    OtpChannel,
    OtpVerification,
)
from kefe_api.modules.identity.account_ports import AccountSessionMaterialFactory
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository


class InMemoryAccountContinuityRepository:
    def __init__(self, identity_repository: InMemoryIdentityRepository) -> None:
        self._identity = identity_repository
        self._challenges: dict[UUID, OtpChallenge] = {}
        self._verifications: dict[str, OtpVerification] = {}
        self._accounts: dict[str, AccountIdentity] = {}
        self._merged_into: dict[UUID, UUID] = {}
        self._guest_merge_replays: dict[str, GuestMergeReplay] = {}
        self._lock = RLock()

    def create_challenge(self, challenge: OtpChallenge) -> None:
        with self._lock:
            self._challenges[challenge.id] = challenge

    def get_challenge(self, challenge_id: UUID) -> OtpChallenge | None:
        with self._lock:
            return self._challenges.get(challenge_id)

    def record_failed_attempt(self, challenge_id: UUID) -> int:
        with self._lock:
            challenge = self._challenges[challenge_id]
            updated = OtpChallenge(
                id=challenge.id,
                channel=challenge.channel,
                identifier_hash=challenge.identifier_hash,
                identifier_hint=challenge.identifier_hint,
                code_hash=challenge.code_hash,
                requested_at=challenge.requested_at,
                expires_at=challenge.expires_at,
                consumed_at=challenge.consumed_at,
                failed_attempts=challenge.failed_attempts + 1,
            )
            self._challenges[challenge_id] = updated
            return updated.failed_attempts

    def consume_challenge(
        self,
        *,
        challenge_id: UUID,
        consumed_at: datetime,
        verification: OtpVerification,
    ) -> bool:
        with self._lock:
            challenge = self._challenges.get(challenge_id)
            if challenge is None or challenge.consumed_at is not None:
                return False
            self._challenges[challenge_id] = OtpChallenge(
                id=challenge.id,
                channel=challenge.channel,
                identifier_hash=challenge.identifier_hash,
                identifier_hint=challenge.identifier_hint,
                code_hash=challenge.code_hash,
                requested_at=challenge.requested_at,
                expires_at=challenge.expires_at,
                consumed_at=consumed_at,
                failed_attempts=challenge.failed_attempts,
            )
            self._verifications[verification.token_hash] = verification
            return True

    def consume_verification(
        self,
        *,
        token_hash: str,
        now: datetime,
    ) -> OtpVerification | None:
        with self._lock:
            verification = self._verifications.get(token_hash)
            if (
                verification is None
                or verification.consumed_at is not None
                or verification.expires_at <= now
            ):
                return None
            consumed = OtpVerification(
                token_hash=verification.token_hash,
                identifier_hash=verification.identifier_hash,
                channel=verification.channel,
                identifier_hint=verification.identifier_hint,
                verified_at=verification.verified_at,
                expires_at=verification.expires_at,
                consumed_at=now,
            )
            self._verifications[token_hash] = consumed
            return verification

    def get_account_by_identifier(self, identifier_hash: str) -> AccountIdentity | None:
        with self._lock:
            return self._accounts.get(identifier_hash)

    def get_guest_merge_replay(
        self,
        verification_token_hash: str,
    ) -> GuestMergeReplay | None:
        with self._lock:
            return self._guest_merge_replays.get(verification_token_hash)

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
        with self._lock:
            existing = self._guest_merge_replays.get(verification_token_hash)
            if existing is not None:
                self._require_matching_source(existing, source_actor_id)
                return existing

            verification = self.consume_verification(
                token_hash=verification_token_hash,
                now=completed_at,
            )
            if verification is None:
                existing = self._guest_merge_replays.get(verification_token_hash)
                if existing is not None:
                    self._require_matching_source(existing, source_actor_id)
                    return existing
                raise DomainError(
                    "AUTH_VERIFICATION_INVALID",
                    "Verification token is invalid or expired",
                    401,
                )

            account_actor_id, merged_from_actor_id = self.upgrade_or_merge_guest(
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
                self.create_account_session(
                    actor_id=account_actor_id,
                    token_hash=account_token_hash,
                    expires_at=account_session_expires_at,
                )
            else:
                self._identity.create_account_session(
                    actor_id=account_actor_id,
                    session_id=material.session_id,
                    token_hash=material.access_token_hash,
                    expires_at=material.access_expires_at,
                    renewal_token_hash=material.renewal_token_hash,
                    rotation_counter=material.rotation_counter,
                    token_derivation_key_id=material.derivation_key_id,
                    continuity_absolute_expires_at=material.continuity_absolute_expires_at,
                    continuity_inactive_expires_at=material.continuity_inactive_expires_at,
                )
            replay = GuestMergeReplay(
                verification_token_hash=verification_token_hash,
                source_actor_id=source_actor_id,
                account_actor_id=account_actor_id,
                merged_from_actor_id=merged_from_actor_id,
                account_session_expires_at=(
                    material.access_expires_at
                    if material is not None
                    else account_session_expires_at
                ),
                completed_at=completed_at,
                account_session_id=material.session_id if material is not None else None,
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
            self._guest_merge_replays[verification_token_hash] = replay
            return replay

    def upgrade_or_merge_guest(
        self,
        *,
        guest_actor_id: UUID,
        identifier_hash: str,
        channel: OtpChannel,
        identifier_hint: str,
        verified_at: datetime,
    ) -> tuple[UUID, UUID | None]:
        with self._lock:
            existing = self._accounts.get(identifier_hash)
            if existing is not None and existing.actor_id != guest_actor_id:
                self._merged_into[guest_actor_id] = existing.actor_id
                self._identity.promote_or_merge_actor(
                    guest_actor_id=guest_actor_id,
                    account_actor_id=existing.actor_id,
                    now=verified_at,
                )
                return existing.actor_id, guest_actor_id
            self._identity.promote_or_merge_actor(
                guest_actor_id=guest_actor_id,
                account_actor_id=guest_actor_id,
                now=verified_at,
            )
            account = AccountIdentity(
                actor_id=guest_actor_id,
                identifier_hash=identifier_hash,
                channel=channel,
                identifier_hint=identifier_hint,
                verified_at=verified_at,
            )
            self._accounts[identifier_hash] = account
            return guest_actor_id, None

    def create_account_session(
        self,
        *,
        actor_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        with self._lock:
            self._identity.create_account_session(
                actor_id=actor_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )

    @staticmethod
    def _require_matching_source(replay: GuestMergeReplay, source_actor_id: UUID) -> None:
        if replay.source_actor_id != source_actor_id:
            raise DomainError(
                "AUTH_MERGE_REPLAY_MISMATCH",
                "Completed account conversion belongs to a different source identity",
                409,
            )
