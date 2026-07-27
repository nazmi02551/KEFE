from __future__ import annotations

import hashlib
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from threading import RLock
from typing import Protocol

from kefe_api.core.errors import DomainError


class ClientPlatform(StrEnum):
    IOS = "IOS"
    ANDROID = "ANDROID"
    WEB = "WEB"
    UNKNOWN = "UNKNOWN"


class IntegrityState(StrEnum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    INVALID = "INVALID"
    UNAVAILABLE = "UNAVAILABLE"


class IntegrityMode(StrEnum):
    OFF = "OFF"
    OPTIONAL = "OPTIONAL"
    REQUIRED = "REQUIRED"


@dataclass(frozen=True, slots=True)
class DeviceIntegrityAssessment:
    state: IntegrityState
    provider_code: str | None = None


@dataclass(frozen=True, slots=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


@dataclass(frozen=True, slots=True)
class GuestAdmissionContext:
    source_key: str
    platform: ClientPlatform
    integrity_evidence: str | None


class DeviceIntegrityVerifier(Protocol):
    def verify(
        self,
        *,
        platform: ClientPlatform,
        evidence: str | None,
    ) -> DeviceIntegrityAssessment: ...


class GuestIssueRateLimiter(Protocol):
    def consume(
        self,
        *,
        subject_key: str,
        now: datetime,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision: ...


class UnconfiguredDeviceIntegrityVerifier:
    """Provider-neutral placeholder. It never claims a device is verified."""

    def verify(
        self,
        *,
        platform: ClientPlatform,
        evidence: str | None,
    ) -> DeviceIntegrityAssessment:
        del platform, evidence
        return DeviceIntegrityAssessment(IntegrityState.UNAVAILABLE)


class InMemoryGuestIssueRateLimiter:
    """Single-process limiter for development/tests; production needs a shared adapter."""

    def __init__(self) -> None:
        self._entries: dict[str, deque[datetime]] = defaultdict(deque)
        self._lock = RLock()

    def consume(
        self,
        *,
        subject_key: str,
        now: datetime,
        limit: int,
        window_seconds: int,
    ) -> RateLimitDecision:
        cutoff = now - timedelta(seconds=window_seconds)
        with self._lock:
            entries = self._entries[subject_key]
            while entries and entries[0] <= cutoff:
                entries.popleft()
            if len(entries) >= limit:
                retry_at = entries[0] + timedelta(seconds=window_seconds)
                retry_after = max(1, int((retry_at - now).total_seconds()))
                return RateLimitDecision(False, retry_after)
            entries.append(now)
            return RateLimitDecision(True)


class GuestAdmissionGuard:
    def __init__(
        self,
        *,
        limiter: GuestIssueRateLimiter,
        integrity_verifier: DeviceIntegrityVerifier,
        rate_limit: int,
        rate_window_seconds: int,
        integrity_mode: IntegrityMode,
    ) -> None:
        self._limiter = limiter
        self._integrity_verifier = integrity_verifier
        self._rate_limit = rate_limit
        self._rate_window_seconds = rate_window_seconds
        self._integrity_mode = integrity_mode

    def authorize(self, context: GuestAdmissionContext) -> DeviceIntegrityAssessment:
        now = datetime.now(UTC)
        subject_key = hashlib.sha256(context.source_key.encode("utf-8")).hexdigest()
        limit = self._limiter.consume(
            subject_key=subject_key,
            now=now,
            limit=self._rate_limit,
            window_seconds=self._rate_window_seconds,
        )
        if not limit.allowed:
            raise DomainError(
                "AUTH_GUEST_RATE_LIMITED",
                "Guest credential issuance rate limited",
                429,
                retryable=True,
                meta={"retry_after_seconds": limit.retry_after_seconds},
            )

        if self._integrity_mode is IntegrityMode.OFF:
            return DeviceIntegrityAssessment(IntegrityState.UNVERIFIED)

        assessment = self._integrity_verifier.verify(
            platform=context.platform,
            evidence=context.integrity_evidence,
        )
        if assessment.state is IntegrityState.INVALID:
            raise DomainError(
                "AUTH_DEVICE_INTEGRITY_FAILED",
                "Device integrity verification failed",
                403,
            )
        if (
            self._integrity_mode is IntegrityMode.REQUIRED
            and assessment.state is not IntegrityState.VERIFIED
        ):
            raise DomainError(
                "AUTH_DEVICE_INTEGRITY_REQUIRED",
                "Verified device integrity is required",
                403,
            )
        return assessment
