from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.account_in_memory import (
    InMemoryAccountContinuityRepository,
)
from kefe_api.modules.identity.account_models import OtpChallenge, OtpChannel
from kefe_api.modules.identity.in_memory import InMemoryIdentityRepository


@dataclass(frozen=True, slots=True)
class OtpRequestAbusePolicy:
    cooldown: timedelta
    window: timedelta
    window_limit: int
    retention: timedelta

    @classmethod
    def from_seconds(
        cls,
        *,
        cooldown_seconds: int,
        window_seconds: int,
        window_limit: int,
        retention_seconds: int,
    ) -> OtpRequestAbusePolicy:
        if cooldown_seconds < 1:
            raise ValueError("OTP request cooldown must be positive")
        if window_seconds < cooldown_seconds:
            raise ValueError("OTP request window cannot be shorter than cooldown")
        if window_limit < 1:
            raise ValueError("OTP request window limit must be positive")
        if retention_seconds < window_seconds:
            raise ValueError("OTP request guard retention cannot be shorter than window")
        return cls(
            cooldown=timedelta(seconds=cooldown_seconds),
            window=timedelta(seconds=window_seconds),
            window_limit=window_limit,
            retention=timedelta(seconds=retention_seconds),
        )


@dataclass(frozen=True, slots=True)
class _OtpRequestGuardState:
    window_started_at: datetime
    last_requested_at: datetime
    request_count: int
    retention_expires_at: datetime


def otp_request_rate_limited_error() -> DomainError:
    return DomainError(
        "AUTH_RATE_LIMITED",
        "OTP request rate limit exceeded",
        429,
        retryable=True,
    )


class GuardedInMemoryAccountContinuityRepository(
    InMemoryAccountContinuityRepository
):
    def __init__(
        self,
        identity_repository: InMemoryIdentityRepository,
        policy: OtpRequestAbusePolicy,
    ) -> None:
        super().__init__(identity_repository)
        self._otp_request_policy = policy
        self._otp_request_guards: dict[
            tuple[OtpChannel, str],
            _OtpRequestGuardState,
        ] = {}

    def create_challenge(self, challenge: OtpChallenge) -> None:
        with self._lock:
            now = challenge.requested_at
            self._otp_request_guards = {
                key: state
                for key, state in self._otp_request_guards.items()
                if state.retention_expires_at > now
            }
            key = (challenge.channel, challenge.identifier_hash)
            state = self._otp_request_guards.get(key)
            if state is None:
                window_started_at = now
                request_count = 0
            else:
                if now < state.last_requested_at + self._otp_request_policy.cooldown:
                    raise otp_request_rate_limited_error()
                if now >= state.window_started_at + self._otp_request_policy.window:
                    window_started_at = now
                    request_count = 0
                else:
                    window_started_at = state.window_started_at
                    request_count = state.request_count
                if request_count >= self._otp_request_policy.window_limit:
                    raise otp_request_rate_limited_error()

            self._otp_request_guards[key] = _OtpRequestGuardState(
                window_started_at=window_started_at,
                last_requested_at=now,
                request_count=request_count + 1,
                retention_expires_at=now + self._otp_request_policy.retention,
            )
            self._challenges[challenge.id] = challenge
