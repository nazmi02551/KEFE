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
class AccountCredential:
    actor_id: UUID
    access_token: str
    expires_at: datetime
    merged_from_actor_id: UUID | None


@dataclass(frozen=True, slots=True)
class AccountIdentity:
    actor_id: UUID
    identifier_hash: str
    channel: OtpChannel
    identifier_hint: str
    verified_at: datetime
