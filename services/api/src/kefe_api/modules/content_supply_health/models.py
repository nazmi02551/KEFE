from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

MINIMUM_POLICY_COUNT = 0
MAXIMUM_POLICY_COUNT = 1_000_000
MINIMUM_POLICY_SECONDS = 60
MAXIMUM_POLICY_SECONDS = 2_592_000


def _require_utc(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{field_name} must be timezone-aware UTC")


@dataclass(frozen=True, slots=True)
class ContentSupplyHealthPolicy:
    pending_dispatch_attention_threshold: int = 100
    queued_run_attention_threshold: int = 100
    unreviewed_proposal_attention_threshold: int = 100
    recent_non_success_attention_threshold: int = 0
    max_cycle_silence_seconds: int = 900
    failure_window_seconds: int = 3600

    def __post_init__(self) -> None:
        for value, field_name in (
            (
                self.pending_dispatch_attention_threshold,
                "pending_dispatch_attention_threshold",
            ),
            (self.queued_run_attention_threshold, "queued_run_attention_threshold"),
            (
                self.unreviewed_proposal_attention_threshold,
                "unreviewed_proposal_attention_threshold",
            ),
            (
                self.recent_non_success_attention_threshold,
                "recent_non_success_attention_threshold",
            ),
        ):
            if not MINIMUM_POLICY_COUNT <= value <= MAXIMUM_POLICY_COUNT:
                raise ValueError(f"{field_name} is outside the supported range")
        for value, field_name in (
            (self.max_cycle_silence_seconds, "max_cycle_silence_seconds"),
            (self.failure_window_seconds, "failure_window_seconds"),
        ):
            if not MINIMUM_POLICY_SECONDS <= value <= MAXIMUM_POLICY_SECONDS:
                raise ValueError(f"{field_name} is outside the supported range")


@dataclass(frozen=True, slots=True)
class ContentSupplyOperationalFacts:
    as_of: datetime
    active_schedule_count: int = 0
    paused_schedule_count: int = 0
    due_schedule_count: int = 0
    pending_dispatch_count: int = 0
    running_dispatch_count: int = 0
    stale_dispatch_count: int = 0
    recent_dispatch_non_success_count: int = 0
    queued_ingestion_run_count: int = 0
    running_ingestion_run_count: int = 0
    stale_ingestion_lease_count: int = 0
    recent_failed_ingestion_run_count: int = 0
    unreviewed_proposal_count: int = 0
    running_cycle_count: int = 0
    stale_cycle_count: int = 0
    recent_non_success_cycle_count: int = 0
    latest_terminal_cycle_state: str | None = None
    latest_terminal_cycle_completed_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_utc(self.as_of, "as_of")
        count_fields = (
            "active_schedule_count",
            "paused_schedule_count",
            "due_schedule_count",
            "pending_dispatch_count",
            "running_dispatch_count",
            "stale_dispatch_count",
            "recent_dispatch_non_success_count",
            "queued_ingestion_run_count",
            "running_ingestion_run_count",
            "stale_ingestion_lease_count",
            "recent_failed_ingestion_run_count",
            "unreviewed_proposal_count",
            "running_cycle_count",
            "stale_cycle_count",
            "recent_non_success_cycle_count",
        )
        for field_name in count_fields:
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be non-negative")
        if self.latest_terminal_cycle_completed_at is not None:
            _require_utc(
                self.latest_terminal_cycle_completed_at,
                "latest_terminal_cycle_completed_at",
            )
        if (
            self.latest_terminal_cycle_state is None
            and self.latest_terminal_cycle_completed_at is not None
        ):
            raise ValueError("terminal cycle completion requires a terminal state")
        if (
            self.latest_terminal_cycle_state is not None
            and self.latest_terminal_cycle_completed_at is None
        ):
            raise ValueError("terminal cycle state requires completion time")


class ContentSupplyHealthSignal(StrEnum):
    QUIET = "QUIET"
    NOMINAL = "NOMINAL"
    ATTENTION = "ATTENTION"
    CRITICAL = "CRITICAL"


class ContentSupplyHealthReason(StrEnum):
    STALE_SOURCE_DISPATCH = "STALE_SOURCE_DISPATCH"
    STALE_INGESTION_LEASE = "STALE_INGESTION_LEASE"
    STALE_CONTENT_SUPPLY_CYCLE = "STALE_CONTENT_SUPPLY_CYCLE"
    SOURCE_DISPATCH_BACKLOG = "SOURCE_DISPATCH_BACKLOG"
    INGESTION_RUN_BACKLOG = "INGESTION_RUN_BACKLOG"
    PROPOSAL_REVIEW_BACKLOG = "PROPOSAL_REVIEW_BACKLOG"
    RECENT_SOURCE_DISPATCH_NON_SUCCESS = "RECENT_SOURCE_DISPATCH_NON_SUCCESS"
    RECENT_INGESTION_FAILURE = "RECENT_INGESTION_FAILURE"
    RECENT_CONTENT_SUPPLY_CYCLE_NON_SUCCESS = (
        "RECENT_CONTENT_SUPPLY_CYCLE_NON_SUCCESS"
    )
    LATEST_CONTENT_SUPPLY_CYCLE_NON_SUCCESS = (
        "LATEST_CONTENT_SUPPLY_CYCLE_NON_SUCCESS"
    )
    CONTENT_SUPPLY_CYCLE_SILENT = "CONTENT_SUPPLY_CYCLE_SILENT"


@dataclass(frozen=True, slots=True)
class ContentSupplyHealthSnapshot:
    signal: ContentSupplyHealthSignal
    as_of: datetime
    reason_codes: tuple[str, ...]
    active_schedule_count: int
    paused_schedule_count: int
    due_schedule_count: int
    pending_dispatch_count: int
    running_dispatch_count: int
    stale_dispatch_count: int
    recent_dispatch_non_success_count: int
    queued_ingestion_run_count: int
    running_ingestion_run_count: int
    stale_ingestion_lease_count: int
    recent_failed_ingestion_run_count: int
    unreviewed_proposal_count: int
    running_cycle_count: int
    stale_cycle_count: int
    recent_non_success_cycle_count: int
    latest_terminal_cycle_state: str | None
    latest_terminal_cycle_completed_at: datetime | None
    seconds_since_latest_terminal_cycle: int | None

    def __post_init__(self) -> None:
        _require_utc(self.as_of, "as_of")
        if tuple(sorted(set(self.reason_codes))) != self.reason_codes:
            raise ValueError("reason_codes must be sorted and unique")
        if self.seconds_since_latest_terminal_cycle is not None:
            if self.seconds_since_latest_terminal_cycle < 0:
                raise ValueError(
                    "seconds_since_latest_terminal_cycle must be non-negative"
                )

    def as_operational_dict(self) -> dict[str, object]:
        return {
            "signal": self.signal.value,
            "as_of": self.as_of.isoformat(),
            "reason_codes": list(self.reason_codes),
            "active_schedule_count": self.active_schedule_count,
            "paused_schedule_count": self.paused_schedule_count,
            "due_schedule_count": self.due_schedule_count,
            "pending_dispatch_count": self.pending_dispatch_count,
            "running_dispatch_count": self.running_dispatch_count,
            "stale_dispatch_count": self.stale_dispatch_count,
            "recent_dispatch_non_success_count": (
                self.recent_dispatch_non_success_count
            ),
            "queued_ingestion_run_count": self.queued_ingestion_run_count,
            "running_ingestion_run_count": self.running_ingestion_run_count,
            "stale_ingestion_lease_count": self.stale_ingestion_lease_count,
            "recent_failed_ingestion_run_count": (
                self.recent_failed_ingestion_run_count
            ),
            "unreviewed_proposal_count": self.unreviewed_proposal_count,
            "running_cycle_count": self.running_cycle_count,
            "stale_cycle_count": self.stale_cycle_count,
            "recent_non_success_cycle_count": self.recent_non_success_cycle_count,
            "latest_terminal_cycle_state": self.latest_terminal_cycle_state,
            "latest_terminal_cycle_completed_at": (
                self.latest_terminal_cycle_completed_at.isoformat()
                if self.latest_terminal_cycle_completed_at is not None
                else None
            ),
            "seconds_since_latest_terminal_cycle": (
                self.seconds_since_latest_terminal_cycle
            ),
        }
