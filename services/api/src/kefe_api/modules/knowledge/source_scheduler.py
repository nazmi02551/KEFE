from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from json import dumps
from uuid import UUID

from kefe_api.modules.knowledge.source_acquisition import (
    SourceAcquisitionCommand,
    require_versioned_adapter_code,
)

MINIMUM_INTERVAL_SECONDS = 60
MAXIMUM_INTERVAL_SECONDS = 2_592_000
MINIMUM_DISPATCH_ATTEMPTS = 1
MAXIMUM_DISPATCH_ATTEMPTS = 10
MINIMUM_DISPATCH_TTL_SECONDS = 5
MAXIMUM_DISPATCH_TTL_SECONDS = 900


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


def build_source_schedule_key(
    *,
    adapter_code: str,
    external_locator: str,
    pipeline_code: str,
    pipeline_version: str,
    configuration_hash: str,
    first_due_at: datetime,
    interval_seconds: int,
    max_dispatch_attempts: int,
    taxonomy_version: str | None = None,
    methodology_version: str | None = None,
    locale: str | None = None,
    jurisdiction_code: str | None = None,
) -> str:
    normalized = {
        "adapter_code": adapter_code,
        "external_locator": external_locator,
        "pipeline_code": pipeline_code,
        "pipeline_version": pipeline_version,
        "configuration_hash": configuration_hash,
        "first_due_at": first_due_at.isoformat(),
        "interval_seconds": interval_seconds,
        "max_dispatch_attempts": max_dispatch_attempts,
        "taxonomy_version": taxonomy_version,
        "methodology_version": methodology_version,
        "locale": locale,
        "jurisdiction_code": jurisdiction_code,
    }
    encoded = dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


class SourceAcquisitionScheduleState(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    RETIRED = "RETIRED"


_ALLOWED_SCHEDULE_TRANSITIONS = {
    SourceAcquisitionScheduleState.ACTIVE: frozenset(
        {
            SourceAcquisitionScheduleState.PAUSED,
            SourceAcquisitionScheduleState.RETIRED,
        }
    ),
    SourceAcquisitionScheduleState.PAUSED: frozenset(
        {
            SourceAcquisitionScheduleState.ACTIVE,
            SourceAcquisitionScheduleState.RETIRED,
        }
    ),
    SourceAcquisitionScheduleState.RETIRED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class SourceAcquisitionSchedule:
    id: UUID
    schedule_key: str
    adapter_code: str
    external_locator: str
    pipeline_code: str
    pipeline_version: str
    configuration_hash: str
    interval_seconds: int
    max_dispatch_attempts: int
    state: SourceAcquisitionScheduleState
    next_due_at: datetime
    created_at: datetime
    updated_at: datetime
    taxonomy_version: str | None = None
    methodology_version: str | None = None
    locale: str | None = None
    jurisdiction_code: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.schedule_key, "schedule_key")
        require_versioned_adapter_code(self.adapter_code)
        for value, field_name in (
            (self.external_locator, "external_locator"),
            (self.pipeline_code, "pipeline_code"),
            (self.pipeline_version, "pipeline_version"),
            (self.configuration_hash, "configuration_hash"),
        ):
            _require_text(value, field_name)
        for value, field_name in (
            (self.taxonomy_version, "taxonomy_version"),
            (self.methodology_version, "methodology_version"),
            (self.locale, "locale"),
            (self.jurisdiction_code, "jurisdiction_code"),
        ):
            if value is not None:
                _require_text(value, field_name)
        if not MINIMUM_INTERVAL_SECONDS <= self.interval_seconds <= MAXIMUM_INTERVAL_SECONDS:
            raise ValueError("interval_seconds is outside the supported range")
        if not (
            MINIMUM_DISPATCH_ATTEMPTS
            <= self.max_dispatch_attempts
            <= MAXIMUM_DISPATCH_ATTEMPTS
        ):
            raise ValueError("max_dispatch_attempts is outside the supported range")
        _require_utc(self.next_due_at, "next_due_at")
        _require_utc(self.created_at, "created_at")
        _require_utc(self.updated_at, "updated_at")

    def transition(
        self,
        target: SourceAcquisitionScheduleState,
        *,
        at: datetime,
    ) -> SourceAcquisitionSchedule:
        _require_utc(at, "at")
        if target not in _ALLOWED_SCHEDULE_TRANSITIONS[self.state]:
            raise ValueError(f"invalid schedule transition: {self.state} -> {target}")
        return replace(self, state=target, updated_at=at)

    def advance_after_planning(
        self,
        *,
        at: datetime,
    ) -> SourceAcquisitionSchedule:
        _require_utc(at, "at")
        if self.state is not SourceAcquisitionScheduleState.ACTIVE:
            raise ValueError("only ACTIVE schedules may be planned")
        return replace(
            self,
            next_due_at=self.next_due_at + self.interval_delta,
            updated_at=at,
        )

    @property
    def interval_delta(self) -> timedelta:
        return timedelta(seconds=self.interval_seconds)

    def acquisition_command(self) -> SourceAcquisitionCommand:
        return SourceAcquisitionCommand(
            adapter_code=self.adapter_code,
            external_locator=self.external_locator,
            pipeline_code=self.pipeline_code,
            pipeline_version=self.pipeline_version,
            configuration_hash=self.configuration_hash,
            taxonomy_version=self.taxonomy_version,
            methodology_version=self.methodology_version,
            locale=self.locale,
            jurisdiction_code=self.jurisdiction_code,
        )


class SourceAcquisitionDispatchState(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    RETRYABLE_FAILURE = "RETRYABLE_FAILURE"
    FINAL_FAILURE = "FINAL_FAILURE"
    BLOCKED = "BLOCKED"


_TERMINAL_DISPATCH_STATES = frozenset(
    {
        SourceAcquisitionDispatchState.SUCCEEDED,
        SourceAcquisitionDispatchState.RETRYABLE_FAILURE,
        SourceAcquisitionDispatchState.FINAL_FAILURE,
        SourceAcquisitionDispatchState.BLOCKED,
    }
)


@dataclass(frozen=True, slots=True)
class SourceAcquisitionDispatch:
    id: UUID
    schedule_id: UUID
    due_at: datetime
    state: SourceAcquisitionDispatchState
    attempt_count: int
    created_at: datetime
    updated_at: datetime
    worker_ref: str | None = None
    claimed_at: datetime | None = None
    heartbeat_at: datetime | None = None
    expires_at: datetime | None = None
    completed_at: datetime | None = None
    source_artifact_id: UUID | None = None
    ingestion_run_id: UUID | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        _require_utc(self.due_at, "due_at")
        _require_utc(self.created_at, "created_at")
        _require_utc(self.updated_at, "updated_at")
        if self.attempt_count < 0:
            raise ValueError("attempt_count must be >= 0")
        if self.state is SourceAcquisitionDispatchState.PENDING:
            self._require_unowned_uncompleted()
        elif self.state is SourceAcquisitionDispatchState.RUNNING:
            if self.worker_ref is None:
                raise ValueError("RUNNING dispatch requires worker_ref")
            _require_text(self.worker_ref, "worker_ref")
            for value, field_name in (
                (self.claimed_at, "claimed_at"),
                (self.heartbeat_at, "heartbeat_at"),
                (self.expires_at, "expires_at"),
            ):
                if value is None:
                    raise ValueError(f"RUNNING dispatch requires {field_name}")
                _require_utc(value, field_name)
            if self.attempt_count < 1:
                raise ValueError("RUNNING dispatch requires attempt_count >= 1")
            if any(
                value is not None
                for value in (
                    self.completed_at,
                    self.source_artifact_id,
                    self.ingestion_run_id,
                    self.error_code,
                )
            ):
                raise ValueError("RUNNING dispatch cannot contain completion fields")
        elif self.state is SourceAcquisitionDispatchState.SUCCEEDED:
            if self.completed_at is None:
                raise ValueError("SUCCEEDED dispatch requires completed_at")
            _require_utc(self.completed_at, "completed_at")
            if self.source_artifact_id is None or self.ingestion_run_id is None:
                raise ValueError("SUCCEEDED dispatch requires artifact and run identifiers")
            if self.error_code is not None:
                raise ValueError("SUCCEEDED dispatch cannot contain error_code")
        elif self.state in _TERMINAL_DISPATCH_STATES:
            if self.completed_at is None:
                raise ValueError("failed dispatch requires completed_at")
            _require_utc(self.completed_at, "completed_at")
            if self.error_code is None:
                raise ValueError("failed dispatch requires error_code")
            _require_text(self.error_code, "error_code")
            if self.source_artifact_id is not None or self.ingestion_run_id is not None:
                raise ValueError("failed dispatch cannot contain result identifiers")

    def _require_unowned_uncompleted(self) -> None:
        if any(
            value is not None
            for value in (
                self.worker_ref,
                self.claimed_at,
                self.heartbeat_at,
                self.expires_at,
                self.completed_at,
                self.source_artifact_id,
                self.ingestion_run_id,
                self.error_code,
            )
        ):
            raise ValueError("PENDING dispatch must be unowned and uncompleted")

    def claim(
        self,
        *,
        worker_ref: str,
        claimed_at: datetime,
        expires_at: datetime,
    ) -> SourceAcquisitionDispatch:
        if self.state is not SourceAcquisitionDispatchState.PENDING:
            raise ValueError("only PENDING dispatch may be claimed")
        _require_text(worker_ref, "worker_ref")
        _require_utc(claimed_at, "claimed_at")
        _require_utc(expires_at, "expires_at")
        if expires_at <= claimed_at:
            raise ValueError("dispatch expiry must be after claim time")
        return replace(
            self,
            state=SourceAcquisitionDispatchState.RUNNING,
            attempt_count=self.attempt_count + 1,
            worker_ref=worker_ref,
            claimed_at=claimed_at,
            heartbeat_at=claimed_at,
            expires_at=expires_at,
            updated_at=claimed_at,
        )

    def heartbeat(
        self,
        *,
        worker_ref: str,
        at: datetime,
        expires_at: datetime,
    ) -> SourceAcquisitionDispatch:
        self.require_active_owner(worker_ref=worker_ref, at=at)
        _require_utc(expires_at, "expires_at")
        if expires_at <= at:
            raise ValueError("dispatch expiry must be after heartbeat time")
        return replace(
            self,
            heartbeat_at=at,
            expires_at=expires_at,
            updated_at=at,
        )

    def require_active_owner(self, *, worker_ref: str, at: datetime) -> None:
        _require_text(worker_ref, "worker_ref")
        _require_utc(at, "at")
        if self.state is not SourceAcquisitionDispatchState.RUNNING:
            raise ValueError("dispatch is not RUNNING")
        if self.worker_ref != worker_ref:
            raise ValueError("dispatch belongs to another worker")
        if self.expires_at is None or self.expires_at <= at:
            raise ValueError("dispatch lease is expired")

    def recover_stale(
        self,
        *,
        at: datetime,
        max_attempts: int,
    ) -> SourceAcquisitionDispatch:
        _require_utc(at, "at")
        if self.state is not SourceAcquisitionDispatchState.RUNNING:
            raise ValueError("only RUNNING dispatch may be recovered")
        if self.expires_at is None or self.expires_at > at:
            raise ValueError("dispatch is not stale")
        if self.attempt_count >= max_attempts:
            return replace(
                self,
                state=SourceAcquisitionDispatchState.FINAL_FAILURE,
                worker_ref=None,
                claimed_at=None,
                heartbeat_at=None,
                expires_at=None,
                completed_at=at,
                error_code="SOURCE_DISPATCH_ATTEMPTS_EXHAUSTED",
                updated_at=at,
            )
        return replace(
            self,
            state=SourceAcquisitionDispatchState.PENDING,
            worker_ref=None,
            claimed_at=None,
            heartbeat_at=None,
            expires_at=None,
            updated_at=at,
        )

    def complete(
        self,
        *,
        worker_ref: str,
        at: datetime,
        target_state: SourceAcquisitionDispatchState,
        source_artifact_id: UUID | None = None,
        ingestion_run_id: UUID | None = None,
        error_code: str | None = None,
    ) -> SourceAcquisitionDispatch:
        self.require_active_owner(worker_ref=worker_ref, at=at)
        if target_state not in _TERMINAL_DISPATCH_STATES:
            raise ValueError("dispatch completion requires a terminal state")
        return replace(
            self,
            state=target_state,
            worker_ref=None,
            claimed_at=None,
            heartbeat_at=None,
            expires_at=None,
            completed_at=at,
            source_artifact_id=source_artifact_id,
            ingestion_run_id=ingestion_run_id,
            error_code=error_code,
            updated_at=at,
        )


@dataclass(frozen=True, slots=True)
class SourceAcquisitionDispatchClaim:
    schedule: SourceAcquisitionSchedule
    dispatch: SourceAcquisitionDispatch
