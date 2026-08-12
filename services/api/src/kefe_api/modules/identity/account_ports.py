from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import UUID

from kefe_api.modules.identity.account_models import (
    AccountIdentity,
    AccountSessionMaterial,
    GuestMergeReplay,
    OtpChallenge,
    OtpChannel,
    OtpVerification,
)


class AccountSessionMaterialFactory(Protocol):
    def __call__(
        self,
        *,
        actor_id: UUID,
        now: datetime,
    ) -> AccountSessionMaterial: ...


class AccountContinuityRepository(Protocol):
    def create_challenge(self, challenge: OtpChallenge) -> None: ...

    def get_challenge(self, challenge_id: UUID) -> OtpChallenge | None: ...

    def record_failed_attempt(self, challenge_id: UUID) -> int: ...

    def consume_challenge(
        self,
        *,
        challenge_id: UUID,
        consumed_at: datetime,
        verification: OtpVerification,
    ) -> bool: ...

    def consume_verification(self, *, token_hash: str, now: datetime) -> OtpVerification | None: ...

    def get_account_by_identifier(self, identifier_hash: str) -> AccountIdentity | None: ...

    def get_guest_merge_replay(
        self,
        verification_token_hash: str,
    ) -> GuestMergeReplay | None: ...

    def complete_guest_merge(
        self,
        *,
        source_actor_id: UUID,
        verification_token_hash: str,
        account_token_hash: str,
        account_session_expires_at: datetime,
        completed_at: datetime,
        session_material_factory: AccountSessionMaterialFactory | None = None,
    ) -> GuestMergeReplay: ...

    def upgrade_or_merge_guest(
        self,
        *,
        guest_actor_id: UUID,
        identifier_hash: str,
        channel: OtpChannel,
        identifier_hint: str,
        verified_at: datetime,
    ) -> tuple[UUID, UUID | None]: ...

    def create_account_session(
        self,
        *,
        actor_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None: ...


class OtpDeliveryPort(Protocol):
    def send(
        self,
        *,
        delivery_id: UUID,
        channel: OtpChannel,
        identifier: str,
        code: str,
        expires_at: datetime,
    ) -> None: ...
