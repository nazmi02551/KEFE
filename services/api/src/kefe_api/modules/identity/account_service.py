from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from kefe_api.core.errors import DomainError
from kefe_api.core.settings import (
    DEFAULT_ACCOUNT_MERGE_REPLAY_KEY_ID,
    DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET,
    get_settings,
)
from kefe_api.modules.identity.account_models import (
    AccountCredential,
    AccountSessionMaterial,
    GuestMergeReplay,
    OtpChallenge,
    OtpChannel,
    OtpVerification,
)
from kefe_api.modules.identity.account_ports import AccountContinuityRepository, OtpDeliveryPort
from kefe_api.modules.identity.models import ActorKind, TokenResolution, TokenStatus
from kefe_api.modules.identity.session_renewal import SessionContinuityPolicy, SessionTokenDeriver


@dataclass(frozen=True, slots=True)
class _ReplayKeyReference:
    key_id: str
    derivation_version: int


class AccountContinuityService:
    _LEGACY_MERGE_TOKEN_DOMAIN = "kefe:guest-account-merge:v1"
    _VERSIONED_MERGE_TOKEN_DOMAIN = "kefe:guest-account-merge:v2"
    _VERSIONED_VERIFICATION_PREFIX = "kefe_v2"
    _LEGACY_VERIFICATION_PREFIX = "kefe_v_"
    _KEY_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,63}")

    def __init__(
        self,
        *,
        repository: AccountContinuityRepository,
        delivery: OtpDeliveryPort,
        challenge_ttl_minutes: int = 10,
        verification_ttl_minutes: int = 15,
        account_token_ttl_days: int = 30,
        account_merge_replay_secret: str | None = None,
        account_merge_replay_active_key_id: str | None = None,
        account_merge_replay_retained_keys: Mapping[str, str] | None = None,
        environment: str | None = None,
        max_attempts: int = 5,
    ) -> None:
        runtime_settings = get_settings()
        active_secret = account_merge_replay_secret or runtime_settings.account_merge_replay_secret
        active_key_id = (
            account_merge_replay_active_key_id
            or runtime_settings.account_merge_replay_active_key_id
        )
        retained_keys = dict(
            account_merge_replay_retained_keys
            if account_merge_replay_retained_keys is not None
            else runtime_settings.account_merge_replay_retained_keys
        )
        runtime_environment = environment or runtime_settings.environment
        keyring = self._validated_keyring(
            active_key_id=active_key_id,
            active_secret=active_secret,
            retained_keys=retained_keys,
            environment=runtime_environment,
        )

        self._repo = repository
        self._delivery = delivery
        self._challenge_ttl = timedelta(minutes=challenge_ttl_minutes)
        self._verification_ttl = timedelta(minutes=verification_ttl_minutes)
        self._account_token_ttl = timedelta(days=account_token_ttl_days)
        self._active_replay_key_id = active_key_id
        self._account_merge_replay_keys = {
            key_id: secret.encode() for key_id, secret in keyring.items()
        }
        self._session_policy = SessionContinuityPolicy.from_days(
            access_ttl_days=account_token_ttl_days,
            absolute_lifetime_days=runtime_settings.session_renewal_absolute_lifetime_days,
            inactivity_lifetime_days=runtime_settings.session_renewal_inactivity_days,
            previous_pair_grace_seconds=(
                runtime_settings.session_renewal_previous_pair_grace_seconds
            ),
        )
        self._session_deriver = SessionTokenDeriver(
            active_key_id=runtime_settings.session_renewal_active_key_id,
            active_secret=runtime_settings.session_renewal_secret,
            retained_keys=runtime_settings.session_renewal_retained_keys,
        )
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
            self._delivery.send(
                delivery_id=challenge.id,
                channel=channel,
                identifier=normalized,
                code=code,
                expires_at=challenge.expires_at,
            )
        except Exception:
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

        verification_token = (
            f"{self._VERSIONED_VERIFICATION_PREFIX}."
            f"{self._active_replay_key_id}.{secrets.token_urlsafe(32)}"
        )
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
        normalized_token = verification_token.strip()
        key_reference = self._verification_key_reference(normalized_token)
        verification_token_hash = self._hash_secret(normalized_token)
        now = datetime.now(UTC)
        replay = self._repo.get_guest_merge_replay(verification_token_hash)
        if replay is not None:
            self._validate_replay_actor(authorization, replay)
            return self._credential_from_replay(replay, key_reference=key_reference, now=now)

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

        account_session_expires_at = now + self._account_token_ttl
        candidate_token = self._derive_account_token(
            verification_token_hash=verification_token_hash,
            source_actor_id=principal.actor_id,
            expires_at=account_session_expires_at,
            key_reference=key_reference,
        )
        replay = self._repo.complete_guest_merge(
            source_actor_id=principal.actor_id,
            verification_token_hash=verification_token_hash,
            account_token_hash=self._hash_secret(candidate_token),
            account_session_expires_at=account_session_expires_at,
            completed_at=now,
            session_material_factory=self._build_account_session_material,
        )
        self._validate_replay_actor(authorization, replay)
        return self._credential_from_replay(replay, key_reference=key_reference, now=now)

    def _build_account_session_material(
        self,
        *,
        actor_id: UUID,
        now: datetime,
    ) -> AccountSessionMaterial:
        session_id = uuid4()
        pair = self._session_deriver.derive_pair(
            session_id=session_id,
            actor_id=actor_id,
            actor_kind=ActorKind.ACCOUNT,
            rotation_counter=0,
        )
        absolute_expires_at, inactive_expires_at = self._session_policy.initial_deadlines(now=now)
        return AccountSessionMaterial(
            session_id=session_id,
            access_token_hash=self._hash_secret(pair.access_token),
            renewal_token_hash=self._hash_secret(pair.renewal_token),
            access_expires_at=now + self._account_token_ttl,
            rotation_counter=pair.rotation_counter,
            derivation_key_id=pair.derivation_key_id,
            continuity_absolute_expires_at=absolute_expires_at,
            continuity_inactive_expires_at=inactive_expires_at,
        )

    def _credential_from_replay(
        self,
        replay: GuestMergeReplay,
        *,
        key_reference: _ReplayKeyReference,
        now: datetime,
    ) -> AccountCredential:
        if replay.account_session_expires_at <= now:
            raise DomainError(
                "AUTH_TOKEN_EXPIRED",
                "Completed account conversion replay has expired",
                401,
            )
        if replay.account_session_id is not None and replay.account_session_derivation_key_id:
            pair = self._session_deriver.derive_pair(
                session_id=replay.account_session_id,
                actor_id=replay.account_actor_id,
                actor_kind=ActorKind.ACCOUNT,
                rotation_counter=replay.account_session_rotation_counter,
                key_id=replay.account_session_derivation_key_id,
            )
            return AccountCredential(
                actor_id=replay.account_actor_id,
                access_token=pair.access_token,
                expires_at=replay.account_session_expires_at,
                merged_from_actor_id=replay.merged_from_actor_id,
                renewal_token=pair.renewal_token,
                rotation_counter=pair.rotation_counter,
            )

        access_token = self._derive_account_token(
            verification_token_hash=replay.verification_token_hash,
            source_actor_id=replay.source_actor_id,
            expires_at=replay.account_session_expires_at,
            key_reference=key_reference,
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
        key_reference: _ReplayKeyReference,
    ) -> str:
        replay_key = self._account_merge_replay_keys.get(key_reference.key_id)
        if replay_key is None:
            raise DomainError(
                "DEPENDENCY_TEMPORARILY_UNAVAILABLE",
                "Account conversion replay key is unavailable",
                503,
                retryable=True,
            )
        expiry = expires_at.astimezone(UTC).isoformat(timespec="microseconds")
        if key_reference.derivation_version == 1:
            message = (
                f"{self._LEGACY_MERGE_TOKEN_DOMAIN}:{verification_token_hash}:"
                f"{source_actor_id}:{expiry}"
            ).encode()
        else:
            message = (
                f"{self._VERSIONED_MERGE_TOKEN_DOMAIN}:{key_reference.key_id}:"
                f"{verification_token_hash}:{source_actor_id}:{expiry}"
            ).encode()
        digest = hmac.new(replay_key, message, hashlib.sha256).digest()
        encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return f"kefe_a_{encoded}"

    @classmethod
    def _verification_key_reference(cls, token: str) -> _ReplayKeyReference:
        if token.startswith(f"{cls._VERSIONED_VERIFICATION_PREFIX}."):
            parts = token.split(".", 2)
            if (
                len(parts) != 3
                or cls._KEY_ID_PATTERN.fullmatch(parts[1]) is None
                or len(parts[2]) < 32
            ):
                raise DomainError(
                    "AUTH_VERIFICATION_INVALID",
                    "Verification token is invalid or expired",
                    401,
                )
            return _ReplayKeyReference(key_id=parts[1], derivation_version=2)
        if token.startswith(cls._LEGACY_VERIFICATION_PREFIX) and len(token) >= 32:
            return _ReplayKeyReference(
                key_id=DEFAULT_ACCOUNT_MERGE_REPLAY_KEY_ID,
                derivation_version=1,
            )
        raise DomainError(
            "AUTH_VERIFICATION_INVALID",
            "Verification token is invalid or expired",
            401,
        )

    @classmethod
    def _validated_keyring(
        cls,
        *,
        active_key_id: str,
        active_secret: str,
        retained_keys: Mapping[str, str],
        environment: str,
    ) -> dict[str, str]:
        if cls._KEY_ID_PATTERN.fullmatch(active_key_id) is None:
            raise ValueError("account merge replay active key id is invalid")
        if active_key_id in retained_keys:
            raise ValueError("account merge replay active key id is duplicated")

        keyring = {active_key_id: active_secret, **retained_keys}
        seen_secrets: set[str] = set()
        production = environment.strip().lower() == "production"
        for key_id, secret in keyring.items():
            if cls._KEY_ID_PATTERN.fullmatch(key_id) is None:
                raise ValueError("account merge replay retained key id is invalid")
            if secret != secret.strip() or len(secret) < 32:
                raise ValueError(
                    "account merge replay secrets must contain at least 32 unpadded characters"
                )
            if secret in seen_secrets:
                raise ValueError("account merge replay key secrets must be unique")
            if production and secret == DEVELOPMENT_ACCOUNT_MERGE_REPLAY_SECRET:
                raise ValueError(
                    "production requires account merge replay keys from secret management"
                )
            seen_secrets.add(secret)
        return keyring

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
