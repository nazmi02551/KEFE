from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.core.settings import (
    DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET,
    get_settings,
)
from kefe_api.modules.identity.account_models import (
    AccountCredential,
    GuestMergeReplay,
    OtpChallenge,
    OtpChannel,
    OtpVerification,
)
from kefe_api.modules.identity.account_ports import AccountContinuityRepository, OtpDeliveryPort
from kefe_api.modules.identity.models import ActorKind, TokenResolution, TokenStatus


class AccountContinuityService:
    _MERGE_TOKEN_DOMAIN = "kefe:guest-account-merge:v1"

    def __init__(
        self,
        *,
        repository: AccountContinuityRepository,
        delivery: OtpDeliveryPort,
        challenge_ttl_minutes: int = 10,
        verification_ttl_minutes: int = 15,
        account_token_ttl_days: int = 30,
        account_merge_replay_secret: str | None = None,
        environment: str | None = None,
        max_attempts: int = 5,
    ) -> None:
        runtime_settings = get_settings()
        replay_secret = (
            account_merge_replay_secret
            or runtime_settings.account_merge_replay_secret
        )
        runtime_environment = environment or runtime_settings.environment
        if (
            runtime_environment.strip().lower() == "production"
            and replay_secret == DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET
        ):
            raise ValueError(
                "production requires KEFE_ACCOUNT_MERGE_REPLAY_SECRET from secret management"
            )
        if len(replay_secret) < 32:
            raise ValueError("account merge replay secret must contain at least 32 characters")
        self._repo = repository
        self._delivery = delivery
        self._challenge_ttl = timedelta(minutes=challenge_ttl_minutes)
        self._verification_ttl = timedelta(minutes=verification_ttl_minutes)
        self._account_token_ttl = timedelta(days=account_token_ttl_days)
        self._account_merge_replay_secret = replay_secret.encode("utf-8")
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
        authorization: TokenResolution,
        verification_token: str,
    ) -> AccountCredential:
        verification_token_hash = self._hash_secret(verification_token.strip())
        replay = self._repo.get_guest_merge_replay(verification_token_hash)
        if replay is not None:
            self._validate_replay_actor(authorization, replay)
            return self._credential_from_replay(replay)

        if authorization.status is TokenStatus.REVOKED:
            raise DomainError("AUTH_TOKEN_REVOKED", "Authentication token revoked", 401)
        principal = authorization.principal
        if authorization.status is not TokenStatus.ACTIVE or principal is None:
            raise DomainError("AUTH_TOKEN_INVALID", "Authentication token invalid", 401)
        if principal.actor_kind is not ActorKind.GUEST:
            raise DomainError(
                "AUTH_GUEST_REQUIRED",
                "Guest identity is required for account conversion",
                409,
            )

        completed_at = datetime.now(UTC)
        account_session_expires_at = completed_at + self._account_token_ttl
        candidate_token = self._derive_account_token(
            verification_token_hash=verification_token_hash,
            source_actor_id=principal.actor_id,
            expires_at=account_session_expires_at,
        )
        replay = self._repo.complete_guest_merge(
            source_actor_id=principal.actor_id,
            verification_token_hash=verification_token_hash,
            account_token_hash=self._hash_secret(candidate_token),
            account_session_expires_at=account_session_expires_at,
            completed_at=completed_at,
        )
        self._validate_replay_actor(authorization, replay)
        return self._credential_from_replay(replay)

    def _credential_from_replay(self, replay: GuestMergeReplay) -> AccountCredential:
        access_token = self._derive_account_token(
            verification_token_hash=replay.verification_token_hash,
            source_actor_id=replay.source_actor_id,
            expires_at=replay.account_session_expires_at,
        )
        return AccountCredential(
            actor_id=replay.account_actor_id,
            access_token=access_token,
            expires_at=replay.account_session_expires_at,
            merged_from_actor_id=replay.merged_from_actor_id,
        )

    @staticmethod
    def _validate_replay_actor(
        authorization: TokenResolution,
        replay: GuestMergeReplay,
    ) -> None:
        principal = authorization.principal
        if principal is None or principal.actor_id != replay.source_actor_id:
            raise DomainError(
                "AUTH_MERGE_REPLAY_MISMATCH",
                "Completed account conversion belongs to a different source identity",
                409,
            )

    def _derive_account_token(
        self,
        *,
        verification_token_hash: str,
        source_actor_id: UUID,
        expires_at: datetime,
    ) -> str:
        expiry = expires_at.astimezone(UTC).isoformat(timespec="microseconds")
        message = (
            f"{self._MERGE_TOKEN_DOMAIN}:{verification_token_hash}:"
            f"{source_actor_id}:{expiry}"
        ).encode()
        digest = hmac.new(
            self._account_merge_replay_secret,
            message,
            hashlib.sha256,
        ).digest()
        encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return f"kefe_a_{encoded}"

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
