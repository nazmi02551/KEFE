from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.account_models import (
    AccountCredential,
    OtpChallenge,
    OtpChannel,
    OtpVerification,
)
from kefe_api.modules.identity.account_ports import AccountContinuityRepository, OtpDeliveryPort
from kefe_api.modules.identity.models import ActorKind, ActorPrincipal


class AccountContinuityService:
    def __init__(
        self,
        *,
        repository: AccountContinuityRepository,
        delivery: OtpDeliveryPort,
        challenge_ttl_minutes: int = 10,
        verification_ttl_minutes: int = 15,
        account_token_ttl_days: int = 30,
        max_attempts: int = 5,
    ) -> None:
        self._repo = repository
        self._delivery = delivery
        self._challenge_ttl = timedelta(minutes=challenge_ttl_minutes)
        self._verification_ttl = timedelta(minutes=verification_ttl_minutes)
        self._account_token_ttl = timedelta(days=account_token_ttl_days)
        self._max_attempts = max_attempts

    def request_otp(self, *, channel: OtpChannel, identifier: str) -> OtpChallenge:
        normalized, hint = self._normalize_identifier(channel, identifier)
        now = datetime.now(UTC)
        code = f"{secrets.randbelow(1_000_000):06d}"
        challenge = OtpChallenge(
            id=uuid4(),
            channel=channel,
            identifier_hash=self._hash_identifier(channel, normalized),
            identifier_hint=hint,
            code_hash=self._hash_secret(code),
            requested_at=now,
            expires_at=now + self._challenge_ttl,
        )
        self._repo.create_challenge(challenge)
        try:
            self._delivery.send(channel=channel, identifier=normalized, code=code)
        except Exception:
            # Persisted challenge is intentionally unusable without successful delivery;
            # callers receive the delivery failure and may request a new challenge later.
            raise
        return challenge

    def verify_otp(self, *, challenge_id: UUID, code: str) -> tuple[str, datetime]:
        challenge = self._repo.get_challenge(challenge_id)
        now = datetime.now(UTC)
        if challenge is None:
            raise DomainError("AUTH_OTP_CHALLENGE_NOT_FOUND", "OTP challenge not found", 404)
        if challenge.consumed_at is not None:
            raise DomainError("AUTH_OTP_CHALLENGE_USED", "OTP challenge already used", 409)
        if challenge.expires_at <= now:
            raise DomainError("AUTH_OTP_EXPIRED", "OTP challenge expired", 410)
        if challenge.failed_attempts >= self._max_attempts:
            raise DomainError("AUTH_OTP_ATTEMPTS_EXCEEDED", "OTP challenge locked", 429)
        normalized_code = code.strip()
        if not re.fullmatch(r"\d{6}", normalized_code) or not hmac.compare_digest(
            challenge.code_hash,
            self._hash_secret(normalized_code),
        ):
            attempts = self._repo.record_failed_attempt(challenge_id)
            if attempts >= self._max_attempts:
                raise DomainError("AUTH_OTP_ATTEMPTS_EXCEEDED", "OTP challenge locked", 429)
            raise DomainError("AUTH_OTP_INVALID", "OTP code is invalid", 422)

        verification_token = f"kefe_v_{secrets.token_urlsafe(32)}"
        verification = OtpVerification(
            token_hash=self._hash_secret(verification_token),
            identifier_hash=challenge.identifier_hash,
            channel=challenge.channel,
            identifier_hint=challenge.identifier_hint,
            verified_at=now,
            expires_at=now + self._verification_ttl,
        )
        if not self._repo.consume_challenge(
            challenge_id=challenge.id,
            consumed_at=now,
            verification=verification,
        ):
            raise DomainError("AUTH_OTP_CHALLENGE_USED", "OTP challenge already used", 409)
        return verification_token, verification.expires_at

    def merge_guest(
        self,
        *,
        principal: ActorPrincipal,
        verification_token: str,
    ) -> AccountCredential:
        if principal.actor_kind is not ActorKind.GUEST:
            raise DomainError(
                "AUTH_GUEST_REQUIRED",
                "Guest identity is required for account conversion",
                409,
            )
        now = datetime.now(UTC)
        verification = self._repo.consume_verification(
            token_hash=self._hash_secret(verification_token.strip()),
            now=now,
        )
        if verification is None:
            raise DomainError(
                "AUTH_VERIFICATION_INVALID",
                "Verification token is invalid or expired",
                401,
            )
        actor_id, merged_from = self._repo.upgrade_or_merge_guest(
            guest_actor_id=principal.actor_id,
            identifier_hash=verification.identifier_hash,
            channel=verification.channel,
            identifier_hint=verification.identifier_hint,
            verified_at=verification.verified_at,
        )
        access_token = f"kefe_a_{secrets.token_urlsafe(32)}"
        expires_at = now + self._account_token_ttl
        self._repo.create_account_session(
            actor_id=actor_id,
            token_hash=self._hash_secret(access_token),
            expires_at=expires_at,
        )
        return AccountCredential(
            actor_id=actor_id,
            access_token=access_token,
            expires_at=expires_at,
            merged_from_actor_id=merged_from,
        )

    @staticmethod
    def _normalize_identifier(channel: OtpChannel, identifier: str) -> tuple[str, str]:
        raw = identifier.strip()
        if channel is OtpChannel.EMAIL:
            normalized = raw.lower()
            if len(normalized) > 254 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
                raise DomainError("AUTH_IDENTIFIER_INVALID", "Email address is invalid", 422)
            local, domain = normalized.split("@", 1)
            hint = f"{local[:2]}***@{domain}"
            return normalized, hint
        digits = re.sub(r"[^0-9+]", "", raw)
        if not re.fullmatch(r"\+?[1-9]\d{7,14}", digits):
            raise DomainError("AUTH_IDENTIFIER_INVALID", "Phone number is invalid", 422)
        normalized = digits if digits.startswith("+") else f"+{digits}"
        hint = f"***{normalized[-4:]}"
        return normalized, hint

    @staticmethod
    def _hash_identifier(channel: OtpChannel, identifier: str) -> str:
        return hashlib.sha256(f"{channel.value}:{identifier}".encode()).hexdigest()

    @staticmethod
    def _hash_secret(value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()
