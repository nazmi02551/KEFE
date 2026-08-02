from __future__ import annotations

import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from kefe_api.modules.knowledge.source_acquisition import (
    require_versioned_adapter_code,
)

_SECRET_REFERENCE = re.compile(
    r"^(?:secret|vault|kms|envref)://[A-Za-z0-9._/@:+-]+$"
)
MINIMUM_QUOTA_LIMIT = 1
MAXIMUM_QUOTA_LIMIT = 100_000
MINIMUM_QUOTA_WINDOW_SECONDS = 1
MAXIMUM_QUOTA_WINDOW_SECONDS = 86_400
MINIMUM_FAILURE_THRESHOLD = 1
MAXIMUM_FAILURE_THRESHOLD = 1_000
MINIMUM_CIRCUIT_OPEN_SECONDS = 1
MAXIMUM_CIRCUIT_OPEN_SECONDS = 86_400
MINIMUM_PERMIT_TTL_SECONDS = 5
MAXIMUM_PERMIT_TTL_SECONDS = 3_600


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def require_secret_reference(secret_ref: str) -> None:
    _require_text(secret_ref, "secret_ref")
    if _SECRET_REFERENCE.fullmatch(secret_ref) is None:
        raise ValueError("secret_ref must use an allowed opaque reference scheme")


class ProviderCredentialMode(StrEnum):
    PUBLIC = "PUBLIC"
    SECRET_REF = "SECRET_REF"


class ProviderCapabilityLifecycle(StrEnum):
    ENABLED = "ENABLED"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


_ALLOWED_LIFECYCLE_TRANSITIONS = {
    ProviderCapabilityLifecycle.ENABLED: frozenset(
        {ProviderCapabilityLifecycle.PAUSED, ProviderCapabilityLifecycle.RETIRED}
    ),
    ProviderCapabilityLifecycle.PAUSED: frozenset(
        {ProviderCapabilityLifecycle.ENABLED, ProviderCapabilityLifecycle.RETIRED}
    ),
    ProviderCapabilityLifecycle.RETIRED: frozenset(),
}


class ProviderCircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass(frozen=True, slots=True)
class SourceProviderCapability:
    adapter_code: str
    credential_mode: ProviderCredentialMode
    secret_ref: str | None
    lifecycle_state: ProviderCapabilityLifecycle
    quota_limit: int
    quota_window_seconds: int
    failure_threshold: int
    circuit_open_seconds: int
    permit_ttl_seconds: int
    window_started_at: datetime
    window_request_count: int
    consecutive_failure_count: int
    circuit_state: ProviderCircuitState
    circuit_opened_at: datetime | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        if type(self.credential_mode) is not ProviderCredentialMode:
            raise ValueError("credential_mode must be an exact ProviderCredentialMode")
        if self.credential_mode is ProviderCredentialMode.PUBLIC:
            if self.secret_ref is not None:
                raise ValueError("PUBLIC provider capability cannot contain secret_ref")
        else:
            if self.secret_ref is None:
                raise ValueError("SECRET_REF provider capability requires secret_ref")
            require_secret_reference(self.secret_ref)
        if not MINIMUM_QUOTA_LIMIT <= self.quota_limit <= MAXIMUM_QUOTA_LIMIT:
            raise ValueError("quota_limit is outside the supported range")
        if not (
            MINIMUM_QUOTA_WINDOW_SECONDS
            <= self.quota_window_seconds
            <= MAXIMUM_QUOTA_WINDOW_SECONDS
        ):
            raise ValueError("quota_window_seconds is outside the supported range")
        if not (
            MINIMUM_FAILURE_THRESHOLD
            <= self.failure_threshold
            <= MAXIMUM_FAILURE_THRESHOLD
        ):
            raise ValueError("failure_threshold is outside the supported range")
        if not (
            MINIMUM_CIRCUIT_OPEN_SECONDS
            <= self.circuit_open_seconds
            <= MAXIMUM_CIRCUIT_OPEN_SECONDS
        ):
            raise ValueError("circuit_open_seconds is outside the supported range")
        if not (
            MINIMUM_PERMIT_TTL_SECONDS
            <= self.permit_ttl_seconds
            <= MAXIMUM_PERMIT_TTL_SECONDS
        ):
            raise ValueError("permit_ttl_seconds is outside the supported range")
        if self.window_request_count < 0:
            raise ValueError("window_request_count must be non-negative")
        if self.consecutive_failure_count < 0:
            raise ValueError("consecutive_failure_count must be non-negative")
        for value, field_name in (
            (self.window_started_at, "window_started_at"),
            (self.created_at, "created_at"),
            (self.updated_at, "updated_at"),
        ):
            _require_utc(value, field_name)
        if self.circuit_state is ProviderCircuitState.CLOSED:
            if self.circuit_opened_at is not None:
                raise ValueError("CLOSED circuit cannot have circuit_opened_at")
        else:
            if self.circuit_opened_at is None:
                raise ValueError("OPEN or HALF_OPEN circuit requires opened_at")
            _require_utc(self.circuit_opened_at, "circuit_opened_at")

    @classmethod
    def create(
        cls,
        *,
        adapter_code: str,
        secret_ref: str | None,
        quota_limit: int,
        quota_window_seconds: int,
        failure_threshold: int,
        circuit_open_seconds: int,
        permit_ttl_seconds: int,
        created_at: datetime,
        credential_mode: ProviderCredentialMode = ProviderCredentialMode.SECRET_REF,
    ) -> SourceProviderCapability:
        return cls(
            adapter_code=adapter_code,
            credential_mode=credential_mode,
            secret_ref=secret_ref,
            lifecycle_state=ProviderCapabilityLifecycle.ENABLED,
            quota_limit=quota_limit,
            quota_window_seconds=quota_window_seconds,
            failure_threshold=failure_threshold,
            circuit_open_seconds=circuit_open_seconds,
            permit_ttl_seconds=permit_ttl_seconds,
            window_started_at=created_at,
            window_request_count=0,
            consecutive_failure_count=0,
            circuit_state=ProviderCircuitState.CLOSED,
            circuit_opened_at=None,
            created_at=created_at,
            updated_at=created_at,
        )

    @property
    def immutable_configuration(self) -> tuple[object, ...]:
        return (
            self.adapter_code,
            self.credential_mode,
            self.secret_ref,
            self.quota_limit,
            self.quota_window_seconds,
            self.failure_threshold,
            self.circuit_open_seconds,
            self.permit_ttl_seconds,
            self.created_at,
        )

    def transition_lifecycle(
        self,
        target: ProviderCapabilityLifecycle,
        *,
        at: datetime,
    ) -> SourceProviderCapability:
        _require_utc(at, "at")
        if target not in _ALLOWED_LIFECYCLE_TRANSITIONS[self.lifecycle_state]:
            raise ValueError(
                f"invalid provider lifecycle transition: "
                f"{self.lifecycle_state} -> {target}"
            )
        return replace(self, lifecycle_state=target, updated_at=at)

    def roll_quota_window(self, *, at: datetime) -> SourceProviderCapability:
        _require_utc(at, "at")
        elapsed = int((at - self.window_started_at).total_seconds())
        if elapsed < self.quota_window_seconds:
            return self
        steps = elapsed // self.quota_window_seconds
        return replace(
            self,
            window_started_at=(
                self.window_started_at
                + timedelta(seconds=steps * self.quota_window_seconds)
            ),
            window_request_count=0,
            updated_at=at,
        )

    def after_expired_permits(
        self,
        *,
        count: int,
        at: datetime,
        included_half_open_probe: bool,
    ) -> SourceProviderCapability:
        if count < 0:
            raise ValueError("expired permit count must be non-negative")
        updated = self
        for index in range(count):
            updated = updated.record_failure(
                at=at,
                was_half_open_probe=included_half_open_probe and index == 0,
            )
        return updated

    def prepare_circuit_for_admission(
        self,
        *,
        at: datetime,
    ) -> SourceProviderCapability:
        _require_utc(at, "at")
        if self.circuit_state is not ProviderCircuitState.OPEN:
            return self
        assert self.circuit_opened_at is not None
        if at < self.circuit_opened_at + timedelta(
            seconds=self.circuit_open_seconds
        ):
            return self
        return replace(
            self,
            circuit_state=ProviderCircuitState.HALF_OPEN,
            updated_at=at,
        )

    def count_admission(self, *, at: datetime) -> SourceProviderCapability:
        _require_utc(at, "at")
        return replace(
            self,
            window_request_count=self.window_request_count + 1,
            updated_at=at,
        )

    def record_success(
        self,
        *,
        at: datetime,
        was_half_open_probe: bool,
    ) -> SourceProviderCapability:
        _require_utc(at, "at")
        if was_half_open_probe or self.circuit_state is ProviderCircuitState.CLOSED:
            return replace(
                self,
                consecutive_failure_count=0,
                circuit_state=ProviderCircuitState.CLOSED,
                circuit_opened_at=None,
                updated_at=at,
            )
        return replace(self, updated_at=at)

    def record_failure(
        self,
        *,
        at: datetime,
        was_half_open_probe: bool,
    ) -> SourceProviderCapability:
        _require_utc(at, "at")
        failures = self.consecutive_failure_count + 1
        should_open = (
            was_half_open_probe
            or self.circuit_state is ProviderCircuitState.HALF_OPEN
            or failures >= self.failure_threshold
        )
        if should_open:
            return replace(
                self,
                consecutive_failure_count=failures,
                circuit_state=ProviderCircuitState.OPEN,
                circuit_opened_at=at,
                updated_at=at,
            )
        if self.circuit_state is ProviderCircuitState.OPEN:
            return replace(
                self,
                consecutive_failure_count=failures,
                updated_at=at,
            )
        return replace(
            self,
            consecutive_failure_count=failures,
            updated_at=at,
        )

    def retry_after_for_open_circuit(self, *, at: datetime) -> int:
        if self.circuit_state is not ProviderCircuitState.OPEN:
            return 0
        assert self.circuit_opened_at is not None
        remaining = (
            self.circuit_opened_at
            + timedelta(seconds=self.circuit_open_seconds)
            - at
        ).total_seconds()
        return max(0, int(remaining + 0.999999))

    def retry_after_for_quota(self, *, at: datetime) -> int:
        remaining = (
            self.window_started_at
            + timedelta(seconds=self.quota_window_seconds)
            - at
        ).total_seconds()
        return max(0, int(remaining + 0.999999))


class ProviderCapturePermitState(StrEnum):
    ACTIVE = "ACTIVE"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


@dataclass(frozen=True, slots=True)
class ProviderCapturePermit:
    id: UUID
    adapter_code: str
    state: ProviderCapturePermitState
    was_half_open_probe: bool
    admitted_at: datetime
    expires_at: datetime
    completed_at: datetime | None = None
    failure_code: str | None = None

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        _require_utc(self.admitted_at, "admitted_at")
        _require_utc(self.expires_at, "expires_at")
        if self.expires_at <= self.admitted_at:
            raise ValueError("permit expiry must be after admission")
        if self.state is ProviderCapturePermitState.ACTIVE:
            if self.completed_at is not None or self.failure_code is not None:
                raise ValueError("ACTIVE permit cannot contain completion fields")
        elif self.state is ProviderCapturePermitState.SUCCEEDED:
            if self.completed_at is None or self.failure_code is not None:
                raise ValueError("SUCCEEDED permit requires clean completion")
            _require_utc(self.completed_at, "completed_at")
        else:
            if self.completed_at is None or self.failure_code is None:
                raise ValueError("FAILED/ABANDONED permit requires failure details")
            _require_utc(self.completed_at, "completed_at")
            _require_text(self.failure_code, "failure_code")

    @classmethod
    def create(
        cls,
        *,
        adapter_code: str,
        admitted_at: datetime,
        expires_at: datetime,
        was_half_open_probe: bool,
    ) -> ProviderCapturePermit:
        return cls(
            id=uuid4(),
            adapter_code=adapter_code,
            state=ProviderCapturePermitState.ACTIVE,
            was_half_open_probe=was_half_open_probe,
            admitted_at=admitted_at,
            expires_at=expires_at,
        )

    def require_active(
        self,
        *,
        adapter_code: str,
        at: datetime,
    ) -> None:
        require_versioned_adapter_code(adapter_code)
        _require_utc(at, "at")
        if self.adapter_code != adapter_code:
            raise ValueError("permit belongs to another adapter")
        if self.state is not ProviderCapturePermitState.ACTIVE:
            raise ValueError("permit is not ACTIVE")
        if self.expires_at <= at:
            raise ValueError("permit is expired")

    def succeed(self, *, adapter_code: str, at: datetime) -> ProviderCapturePermit:
        self.require_active(adapter_code=adapter_code, at=at)
        return replace(
            self,
            state=ProviderCapturePermitState.SUCCEEDED,
            completed_at=at,
        )

    def fail(
        self,
        *,
        adapter_code: str,
        at: datetime,
        failure_code: str,
    ) -> ProviderCapturePermit:
        self.require_active(adapter_code=adapter_code, at=at)
        _require_text(failure_code, "failure_code")
        return replace(
            self,
            state=ProviderCapturePermitState.FAILED,
            completed_at=at,
            failure_code=failure_code,
        )

    def abandon(self, *, at: datetime) -> ProviderCapturePermit:
        _require_utc(at, "at")
        if self.state is not ProviderCapturePermitState.ACTIVE:
            raise ValueError("only ACTIVE permit may be abandoned")
        if self.expires_at > at:
            raise ValueError("permit is not expired")
        return replace(
            self,
            state=ProviderCapturePermitState.ABANDONED,
            completed_at=at,
            failure_code="SOURCE_PROVIDER_PERMIT_EXPIRED",
        )


class ProviderAdmissionOutcome(StrEnum):
    ADMITTED = "ADMITTED"
    NOT_REGISTERED = "NOT_REGISTERED"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"
    RATE_LIMITED = "RATE_LIMITED"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"


@dataclass(frozen=True, slots=True)
class ProviderAdmissionResult:
    outcome: ProviderAdmissionOutcome
    adapter_code: str
    permit_id: UUID | None
    circuit_state: ProviderCircuitState | None
    retry_after_seconds: int | None
    reason_code: str

    def __post_init__(self) -> None:
        require_versioned_adapter_code(self.adapter_code)
        _require_text(self.reason_code, "reason_code")
        if self.outcome is ProviderAdmissionOutcome.ADMITTED:
            if self.permit_id is None or self.circuit_state is None:
                raise ValueError("ADMITTED result requires permit and circuit state")
            if self.retry_after_seconds is not None:
                raise ValueError("ADMITTED result cannot contain retry_after")
        elif self.permit_id is not None:
            raise ValueError("denied admission cannot contain permit_id")
        if self.retry_after_seconds is not None and self.retry_after_seconds < 0:
            raise ValueError("retry_after_seconds must be non-negative")

    def as_operational_dict(self) -> dict[str, str | int | None]:
        return {
            "outcome": self.outcome.value,
            "adapter_code": self.adapter_code,
            "permit_id": str(self.permit_id) if self.permit_id else None,
            "circuit_state": (
                self.circuit_state.value if self.circuit_state else None
            ),
            "retry_after_seconds": self.retry_after_seconds,
            "reason_code": self.reason_code,
        }
