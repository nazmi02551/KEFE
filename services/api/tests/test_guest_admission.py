from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kefe_api.core.errors import DomainError
from kefe_api.modules.identity.admission import (
    ClientPlatform,
    DeviceIntegrityAssessment,
    GuestAdmissionContext,
    GuestAdmissionGuard,
    InMemoryGuestIssueRateLimiter,
    IntegrityMode,
    IntegrityState,
)


class FixedIntegrityVerifier:
    def __init__(self, state: IntegrityState) -> None:
        self._state = state

    def verify(
        self,
        *,
        platform: ClientPlatform,
        evidence: str | None,
    ) -> DeviceIntegrityAssessment:
        del platform, evidence
        return DeviceIntegrityAssessment(self._state, provider_code="test")


def _context(source: str = "203.0.113.10") -> GuestAdmissionContext:
    return GuestAdmissionContext(
        source_key=source,
        platform=ClientPlatform.ANDROID,
        integrity_evidence="opaque-attestation",
    )


def test_guest_issue_rate_limit_blocks_after_limit() -> None:
    guard = GuestAdmissionGuard(
        limiter=InMemoryGuestIssueRateLimiter(),
        integrity_verifier=FixedIntegrityVerifier(IntegrityState.VERIFIED),
        rate_limit=2,
        rate_window_seconds=60,
        integrity_mode=IntegrityMode.OPTIONAL,
    )

    guard.authorize(_context())
    guard.authorize(_context())

    with pytest.raises(DomainError) as error:
        guard.authorize(_context())

    assert error.value.code == "AUTH_GUEST_RATE_LIMITED"
    assert error.value.status_code == 429
    assert error.value.retryable is True
    assert error.value.meta["retry_after_seconds"] >= 1


def test_optional_integrity_allows_unavailable_provider() -> None:
    guard = GuestAdmissionGuard(
        limiter=InMemoryGuestIssueRateLimiter(),
        integrity_verifier=FixedIntegrityVerifier(IntegrityState.UNAVAILABLE),
        rate_limit=10,
        rate_window_seconds=60,
        integrity_mode=IntegrityMode.OPTIONAL,
    )

    assessment = guard.authorize(_context())

    assert assessment.state is IntegrityState.UNAVAILABLE


def test_required_integrity_rejects_unverified_device() -> None:
    guard = GuestAdmissionGuard(
        limiter=InMemoryGuestIssueRateLimiter(),
        integrity_verifier=FixedIntegrityVerifier(IntegrityState.UNVERIFIED),
        rate_limit=10,
        rate_window_seconds=60,
        integrity_mode=IntegrityMode.REQUIRED,
    )

    with pytest.raises(DomainError) as error:
        guard.authorize(_context())

    assert error.value.code == "AUTH_DEVICE_INTEGRITY_REQUIRED"
    assert error.value.status_code == 403


def test_invalid_integrity_is_rejected_even_when_optional() -> None:
    guard = GuestAdmissionGuard(
        limiter=InMemoryGuestIssueRateLimiter(),
        integrity_verifier=FixedIntegrityVerifier(IntegrityState.INVALID),
        rate_limit=10,
        rate_window_seconds=60,
        integrity_mode=IntegrityMode.OPTIONAL,
    )

    with pytest.raises(DomainError) as error:
        guard.authorize(_context())

    assert error.value.code == "AUTH_DEVICE_INTEGRITY_FAILED"
    assert error.value.status_code == 403


def test_integrity_off_does_not_call_provider() -> None:
    class FailingVerifier:
        def verify(self, *, platform: ClientPlatform, evidence: str | None):
            del platform, evidence
            raise AssertionError("provider must not be called when integrity policy is OFF")

    guard = GuestAdmissionGuard(
        limiter=InMemoryGuestIssueRateLimiter(),
        integrity_verifier=FailingVerifier(),
        rate_limit=10,
        rate_window_seconds=60,
        integrity_mode=IntegrityMode.OFF,
    )

    assessment = guard.authorize(_context())
    assert assessment.state is IntegrityState.UNVERIFIED


def test_rate_limiter_subjects_are_independent() -> None:
    limiter = InMemoryGuestIssueRateLimiter()
    now = datetime.now(UTC)

    first = limiter.consume(subject_key="one", now=now, limit=1, window_seconds=60)
    second = limiter.consume(subject_key="two", now=now, limit=1, window_seconds=60)

    assert first.allowed is True
    assert second.allowed is True
