from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class ActorKind(StrEnum):
    GUEST = "GUEST"
    ACCOUNT = "ACCOUNT"


class TokenStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True)
class ActorPrincipal:
    actor_id: UUID
    actor_kind: ActorKind


@dataclass(frozen=True, slots=True)
class GuestCredential:
    actor_id: UUID
    access_token: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class TokenResolution:
    status: TokenStatus
    principal: ActorPrincipal | None = None
