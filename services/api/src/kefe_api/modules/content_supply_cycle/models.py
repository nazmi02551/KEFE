from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from hashlib import sha256
from json import dumps
from uuid import UUID, uuid4

MINIMUM_CYCLE_TTL_SECONDS = 5
MAXIMUM_CYCLE_TTL_SECONDS = 3600
MINIMUM_PHASE_BUDGET = 0
MAXIMUM_PHASE_BUDGET = 100
MINIMUM_PIPELINE_RUN_BUDGET = 1
MAXIMUM_PIPELINE_RUN_BUDGET = 100


def _require_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


@dataclass(frozen=True, slots=True)
class ContentSupplyPipelineTarget:
    pipeline_code: str
    pipeline_version: str
    max_runs: int

    def __post_init__(self) -> None:
        _require_text(self.pipeline_code, "pipeline_code")
        _require_text(self.pipeline_version, "pipeline_version")
        if not (
            MINIMUM_PIPELINE_RUN_BUDGET
            <= self.max_runs
            <= MAXIMUM_PIPELINE_RUN_BUDGET
        ):
            raise ValueError("pipeline max_runs is outside the supported range")

    @property
    def identity(self) -> tuple[str, str]:
        return self.pipeline_code, self.pipeline_version


@dataclass(frozen=True, slots=True)
class ContentSupplyCycleCommand:
    worker_ref: str
    plan_budget: int
    dispatch_budget: int
    pipeline_targets: tuple[ContentSupplyPipelineTarget, ...]
    cycle_ttl_seconds: int
    dispatch_ttl_seconds: int
    ingestion_ttl_seconds: int

    def __post_init__(self) -> None:
        _require_text(self.worker_ref, "worker_ref")
        for value, field_name in (
            (self.plan_budget, "plan_budget"),
            (self.dispatch_budget, "dispatch_budget"),
        ):
            if not MINIMUM_PHASE_BUDGET <= value <= MAXIMUM_PHASE_BUDGET:
                raise ValueError(f"{field_name} is outside the supported range")
        for value, field_name in (
            (self.cycle_ttl_seconds, "cycle_ttl_seconds"),
            (self.dispatch_ttl_seconds, "dispatch_ttl_seconds"),
            (self.ingestion_ttl_seconds, "ingestion_ttl_seconds"),
        ):
            if not MINIMUM_CYCLE_TTL_SECONDS <= value <= MAXIMUM_CYCLE_TTL_SECONDS:
                raise ValueError(f"{field_name} is outside the supported range")
        identities = tuple(target.identity for target in self.pipeline_targets)
        if len(set(identities)) != len(identities):
            raise ValueError("duplicate content-supply pipeline target")

    @property
    def plan_hash(self) -> str:
        encoded = dumps(
            {
                "plan_budget": self.plan_budget,
                "dispatch_budget": self.dispatch_budget,
                "cycle_ttl_seconds": self.cycle_ttl_seconds,
                "dispatch_ttl_seconds": self.dispatch_ttl_seconds,
                "ingestion_ttl_seconds": self.ingestion_ttl_seconds,
                "pipeline_targets": [
                    {
                        "pipeline_code": target.pipeline_code,
                        "pipeline_version": target.pipeline_version,
                        "max_runs": target.max_runs,
                    }
                    for target in self.pipeline_targets
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return sha256(encoded).hexdigest()


class ContentSupplyCycleState(StrEnum):
    RUNNING = "RUNNING"
    IDLE = "IDLE"
    SUCCEEDED = "SUCCEEDED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"


_TERMINAL_STATES = frozenset(
    {
        ContentSupplyCycleState.IDLE,
        ContentSupplyCycleState.SUCCEEDED,
        ContentSupplyCycleState.DEGRADED,
        ContentSupplyCycleState.FAILED,
        ContentSupplyCycleState.ABANDONED,
    }
)


@dataclass(frozen=True, slots=True)
class ContentSupplyCycleCounters:
    planned_count: int = 0
    dispatch_attempted_count: int = 0
    dispatch_succeeded_count: int = 0
    dispatch_non_success_count: int = 0
    ingestion_attempted_count: int = 0
    ingestion_succeeded_count: int = 0
    ingestion_non_success_count: int = 0

    def __post_init__(self) -> None:
        values = (
            self.planned_count,
            self.dispatch_attempted_count,
            self.dispatch_succeeded_count,
            self.dispatch_non_success_count,
            self.ingestion_attempted_count,
            self.ingestion_succeeded_count,
            self.ingestion_non_success_count,
        )
        if any(value < 0 for value in values):
            raise ValueError("content-supply counters must be non-negative")
        if (
            self.dispatch_succeeded_count + self.dispatch_non_success_count
            > self.dispatch_attempted_count
        ):
            raise ValueError("dispatch outcome counts exceed attempted count")
        if (
            self.ingestion_succeeded_count + self.ingestion_non_success_count
            > self.ingestion_attempted_count
        ):
            raise ValueError("ingestion outcome counts exceed attempted count")

    def add_planned(self) -> ContentSupplyCycleCounters:
        return replace(self, planned_count=self.planned_count + 1)

    def add_dispatch(self, *, succeeded: bool) -> ContentSupplyCycleCounters:
        return replace(
            self,
            dispatch_attempted_count=self.dispatch_attempted_count + 1,
            dispatch_succeeded_count=(
                self.dispatch_succeeded_count + (1 if succeeded else 0)
            ),
            dispatch_non_success_count=(
                self.dispatch_non_success_count + (0 if succeeded else 1)
            ),
        )

    def add_ingestion(self, *, succeeded: bool) -> ContentSupplyCycleCounters:
        return replace(
            self,
            ingestion_attempted_count=self.ingestion_attempted_count + 1,
            ingestion_succeeded_count=(
                self.ingestion_succeeded_count + (1 if succeeded else 0)
            ),
            ingestion_non_success_count=(
                self.ingestion_non_success_count + (0 if succeeded else 1)
            ),
        )

    @property
    def total_delegated_attempts(self) -> int:
        return self.dispatch_attempted_count + self.ingestion_attempted_count

    @property
    def has_non_success(self) -> bool:
        return (
            self.dispatch_non_success_count > 0
            or self.ingestion_non_success_count > 0
        )


@dataclass(frozen=True, slots=True)
class ContentSupplyCycle:
    id: UUID
    worker_ref: str
    plan_hash: str
    state: ContentSupplyCycleState
    counters: ContentSupplyCycleCounters
    started_at: datetime
    heartbeat_at: datetime
    expires_at: datetime
    completed_at: datetime | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.worker_ref, "worker_ref")
        _require_text(self.plan_hash, "plan_hash")
        _require_utc(self.started_at, "started_at")
        _require_utc(self.heartbeat_at, "heartbeat_at")
        _require_utc(self.expires_at, "expires_at")
        if self.expires_at <= self.heartbeat_at:
            raise ValueError("cycle expiry must be after heartbeat")
        if self.state is ContentSupplyCycleState.RUNNING:
            if self.completed_at is not None or self.error_code is not None:
                raise ValueError("RUNNING cycle cannot contain terminal fields")
        elif self.state in _TERMINAL_STATES:
            if self.completed_at is None:
                raise ValueError("terminal cycle requires completed_at")
            _require_utc(self.completed_at, "completed_at")
            if self.state in {
                ContentSupplyCycleState.IDLE,
                ContentSupplyCycleState.SUCCEEDED,
            }:
                if self.error_code is not None:
                    raise ValueError("successful cycle cannot contain error_code")
            elif self.error_code is None:
                raise ValueError("non-success terminal cycle requires error_code")
            else:
                _require_text(self.error_code, "error_code")

    @classmethod
    def start(
        cls,
        command: ContentSupplyCycleCommand,
        *,
        started_at: datetime,
        expires_at: datetime,
    ) -> ContentSupplyCycle:
        return cls(
            id=uuid4(),
            worker_ref=command.worker_ref,
            plan_hash=command.plan_hash,
            state=ContentSupplyCycleState.RUNNING,
            counters=ContentSupplyCycleCounters(),
            started_at=started_at,
            heartbeat_at=started_at,
            expires_at=expires_at,
        )

    def require_active_owner(self, *, worker_ref: str, at: datetime) -> None:
        _require_text(worker_ref, "worker_ref")
        _require_utc(at, "at")
        if self.state is not ContentSupplyCycleState.RUNNING:
            raise ValueError("content-supply cycle is not RUNNING")
        if self.worker_ref != worker_ref:
            raise ValueError("content-supply cycle belongs to another worker")
        if self.expires_at <= at:
            raise ValueError("content-supply cycle lease is expired")

    def heartbeat(
        self,
        *,
        worker_ref: str,
        at: datetime,
        expires_at: datetime,
        counters: ContentSupplyCycleCounters,
    ) -> ContentSupplyCycle:
        self.require_active_owner(worker_ref=worker_ref, at=at)
        _require_utc(expires_at, "expires_at")
        if expires_at <= at:
            raise ValueError("cycle expiry must be after heartbeat")
        current = self.counters
        for previous, updated in zip(
            current.__dataclass_fields__,
            counters.__dataclass_fields__,
            strict=True,
        ):
            if getattr(counters, updated) < getattr(current, previous):
                raise ValueError("cycle counters must be monotonic")
        return replace(
            self,
            counters=counters,
            heartbeat_at=at,
            expires_at=expires_at,
        )

    def complete(
        self,
        *,
        worker_ref: str,
        at: datetime,
        state: ContentSupplyCycleState,
        counters: ContentSupplyCycleCounters,
        error_code: str | None = None,
    ) -> ContentSupplyCycle:
        self.require_active_owner(worker_ref=worker_ref, at=at)
        if state not in _TERMINAL_STATES or state is ContentSupplyCycleState.ABANDONED:
            raise ValueError("cycle completion requires a non-abandoned terminal state")
        heartbeat = self.heartbeat(
            worker_ref=worker_ref,
            at=at,
            expires_at=self.expires_at,
            counters=counters,
        )
        return replace(
            heartbeat,
            state=state,
            completed_at=at,
            error_code=error_code,
        )

    def abandon(self, *, at: datetime) -> ContentSupplyCycle:
        _require_utc(at, "at")
        if self.state is not ContentSupplyCycleState.RUNNING:
            raise ValueError("only RUNNING cycle may be abandoned")
        if self.expires_at > at:
            raise ValueError("content-supply cycle is not stale")
        return replace(
            self,
            state=ContentSupplyCycleState.ABANDONED,
            completed_at=at,
            error_code="CONTENT_SUPPLY_CYCLE_STALE",
        )
