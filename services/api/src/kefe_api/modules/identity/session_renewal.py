from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from kefe_api.modules.identity.models import ActorKind


class RenewalTokenMatch(StrEnum):
    CURRENT = "CURRENT"
    PREVIOUS_GRACE = "PREVIOUS_GRACE"


@dataclass(frozen=True, slots=True)
class SessionContinuityPolicy:
    access_ttl: timedelta
    absolute_lifetime: timedelta
    inactivity_lifetime: timedelta
    previous_pair_grace: timedelta

    @classmethod
    def from_days(
        cls,
        *,
        access_ttl_days: int,
        absolute_lifetime_days: int,
        inactivity_lifetime_days: int,
        previous_pair_grace_seconds: int,
    ) -> SessionContinuityPolicy:
        policy = cls(
            access_ttl=timedelta(days=access_ttl_days),
            absolute_lifetime=timedelta(days=absolute_lifetime_days),
            inactivity_lifetime=timedelta(days=inactivity_lifetime_days),
            previous_pair_grace=timedelta(seconds=previous_pair_grace_seconds),
        )
        policy.validate()
        return policy

    def validate(self) -> None:
        if self.access_ttl <= timedelta(0):
            raise ValueError("access TTL must be positive")
        if self.absolute_lifetime <= self.access_ttl:
            raise ValueError("continuity absolute lifetime must exceed access TTL")
        if self.inactivity_lifetime <= self.access_ttl:
            raise ValueError("continuity inactivity lifetime must exceed access TTL")
        if self.inactivity_lifetime > self.absolute_lifetime:
            raise ValueError("continuity inactivity lifetime cannot exceed absolute lifetime")
        if self.previous_pair_grace <= timedelta(0):
            raise ValueError("previous-pair grace must be positive")

    def initial_deadlines(self, *, now: datetime) -> tuple[datetime, datetime]:
        absolute = now + self.absolute_lifetime
        inactive = min(now + self.inactivity_lifetime, absolute)
        return absolute, inactive

    def renewed_inactivity_deadline(
        self,
        *,
        now: datetime,
        absolute_expires_at: datetime,
    ) -> datetime:
        return min(now + self.inactivity_lifetime, absolute_expires_at)


@dataclass(frozen=True, slots=True)
class SessionCredentialPair:
    access_token: str
    renewal_token: str
    rotation_counter: int
    derivation_key_id: str


@dataclass(frozen=True, slots=True)
class SessionRenewalSnapshot:
    session_id: UUID
    actor_id: UUID
    actor_kind: ActorKind
    rotation_counter: int
    derivation_key_id: str
    access_expires_at: datetime
    continuity_absolute_expires_at: datetime
    continuity_inactive_expires_at: datetime
    token_match: RenewalTokenMatch


class SessionTokenDeriver:
    _ACCESS_DOMAIN = b"kefe/session/access/v1"
    _RENEWAL_DOMAIN = b"kefe/session/renewal/v1"

    def __init__(
        self,
        *,
        active_key_id: str,
        active_secret: str,
        retained_keys: dict[str, str] | None = None,
    ) -> None:
        if not active_key_id.strip():
            raise ValueError("session token key id must not be blank")
        if len(active_secret.encode("utf-8")) < 32:
            raise ValueError("session token secret must be at least 32 bytes")
        keys = dict(retained_keys or {})
        keys[active_key_id] = active_secret
        for key_id, secret in keys.items():
            if not key_id.strip():
                raise ValueError("session token key id must not be blank")
            if len(secret.encode("utf-8")) < 32:
                raise ValueError("session token secret must be at least 32 bytes")
        self._active_key_id = active_key_id
        self._keys = keys

    @property
    def active_key_id(self) -> str:
        return self._active_key_id

    def derive_pair(
        self,
        *,
        session_id: UUID,
        actor_id: UUID,
        actor_kind: ActorKind,
        rotation_counter: int,
        key_id: str | None = None,
    ) -> SessionCredentialPair:
        if rotation_counter < 0:
            raise ValueError("rotation counter must be non-negative")
        selected_key_id = key_id or self._active_key_id
        secret = self._keys.get(selected_key_id)
        if secret is None:
            raise ValueError("unknown session token derivation key id")
        material = (
            session_id.bytes
            + actor_id.bytes
            + rotation_counter.to_bytes(8, "big", signed=False)
        )
        access = self._derive(
            secret=secret,
            domain=self._ACCESS_DOMAIN,
            material=material,
        )
        renewal = self._derive(
            secret=secret,
            domain=self._RENEWAL_DOMAIN,
            material=material,
        )
        access_prefix = "kefe_g_" if actor_kind is ActorKind.GUEST else "kefe_a_"
        return SessionCredentialPair(
            access_token=access_prefix + access,
            renewal_token="kefe_r_" + renewal,
            rotation_counter=rotation_counter,
            derivation_key_id=selected_key_id,
        )

    @staticmethod
    def token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _derive(*, secret: str, domain: bytes, material: bytes) -> str:
        digest = hmac.new(
            secret.encode("utf-8"),
            domain + b"\x00" + material,
            hashlib.sha256,
        ).digest()
        return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
