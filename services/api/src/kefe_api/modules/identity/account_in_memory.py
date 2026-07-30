from __future__ import annotations

from datetime import datetime
from uuid import UUID

from kefe_api.modules.identity.account_models import (
    AccountIdentity,
    OtpChallenge,
    OtpChannel,
    OtpVerification,
)
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository


class InMemoryAccountContinuityRepository:
    def __init__(self, identity_repository: InMemoryIdentityRepository) -> None:
        self._identity = identity_repository
        self._challenges: dict[UUID, OtpChallenge] = {}
        self._verifications: dict[str, OtpVerification] = {}
        self._accounts: dict[str, AccountIdentity] = {}
        self._merged_into: dict[UUID, UUID] = {}

    def create_challenge(self, challenge: OtpChallenge) -> None:
        self._challenges[challenge.id] = challenge

    def get_challenge(self, challenge_id: UUID) -> OtpChallenge | None:
        return self._challenges.get(challenge_id)

    def record_failed_attempt(self, challenge_id: UUID) -> int:
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
        return self._accounts.get(identifier_hash)

    def upgrade_or_merge_guest(
        self,
        *,
        guest_actor_id: UUID,
        identifier_hash: str,
        channel: OtpChannel,
        identifier_hint: str,
        verified_at: datetime,
    ) -> tuple[UUID, UUID | None]:
        existing = self._accounts.get(identifier_hash)
        if existing is not None and existing.actor_id != guest_actor_id:
            self._merged_into[guest_actor_id] = existing.actor_id
            self._identity.promote_or_merge_actor(
                guest_actor_id=guest_actor_id,
                account_actor_id=existing.actor_id,
            )
            return existing.actor_id, guest_actor_id
        self._identity.promote_or_merge_actor(
            guest_actor_id=guest_actor_id,
            account_actor_id=guest_actor_id,
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
        self._identity.create_account_session(
            actor_id=actor_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
