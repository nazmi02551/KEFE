from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class OtpChannel(StrEnum):
    EMAIL = "EMAIL"
    SMS = "SMS"


@dataclass(frozen=True, slots=True)
class OtpChallenge:
    id: UUID
    channel: OtpChannel
    identifier_hash: str
    identifier_hint: str
    code_hash: str
    requested_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None
    failed_attempts: int = 0


@dataclass(frozen=True, slots=True)
class OtpVerification:
    token_hash: str
    identifier_hash: str
    channel: OtpChannel
    identifier_hint: str
    verified_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AccountSessionMaterial:
    session_id: UUID
    access_token_hash: str
    renewal_token_hash: str
    access_expires_at: datetime
    rotation_counter: int
    derivation_key_id: str
    continuity_absolute_expires_at: datetime
    continuity_inactive_expires_at: datetime


@dataclass(frozen=True, slots=True)
class AccountCredential:
    actor_id: UUID
    access_token: str
    expires_at: datetime
    merged_from_actor_id: UUID | None
    renewal_token: str | None = None
    rotation_counter: int = 0


@dataclass(frozen=True, slots=True)
class AccountIdentity:
    actor_id: UUID
    identifier_hash: str
    channel: OtpChannel
    identifier_hint: str
    verified_at: datetime


@dataclass(frozen=True, slots=True)
class GuestMergeReplay:
    verification_token_hash: str
    source_actor_id: UUID
    account_actor_id: UUID
    merged_from_actor_id: UUID | None
    account_session_expires_at: datetime
    completed_at: datetime
    account_session_id: UUID | None = None
    account_session_rotation_counter: int = 0
    account_session_derivation_key_id: str | None = None
    continuity_absolute_expires_at: datetime | None = None
    continuity_inactive_expires_at: datetime | None = None
