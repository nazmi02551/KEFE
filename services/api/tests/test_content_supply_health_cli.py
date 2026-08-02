from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from kefe_api.infrastructure.run_content_supply_health_snapshot import (
    INVALID_INPUT_EXIT_CODE,
    exit_code_for,
    main,
    parse_utc_datetime,
)
from kefe_api.modules.content_supply_health.models import (
    ContentSupplyHealthSignal,
    ContentSupplyHealthSnapshot,
)


class CapturingHealthService:
    def __init__(self, signal: ContentSupplyHealthSignal) -> None:
        self.signal = signal
        self.calls = []

    def snapshot(self, policy, *, as_of=None):
        self.calls.append((policy, as_of))
        resolved_as_of = as_of or datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
        return ContentSupplyHealthSnapshot(
            signal=self.signal,
            as_of=resolved_as_of,
            reason_codes=(),
            active_schedule_count=0,
            paused_schedule_count=0,
            due_schedule_count=0,
            pending_dispatch_count=0,
            running_dispatch_count=0,
            stale_dispatch_count=0,
            recent_dispatch_non_success_count=0,
            queued_ingestion_run_count=0,
            running_ingestion_run_count=0,
            stale_ingestion_lease_count=0,
            recent_failed_ingestion_run_count=0,
            unreviewed_proposal_count=0,
            running_cycle_count=0,
            stale_cycle_count=0,
            recent_non_success_cycle_count=0,
            latest_terminal_cycle_state=None,
            latest_terminal_cycle_completed_at=None,
            seconds_since_latest_terminal_cycle=None,
        )


def _factory(service):
    return lambda: SimpleNamespace(
        state=SimpleNamespace(content_supply_health_service=service)
    )


def test_parse_utc_datetime_requires_exact_utc() -> None:
    assert parse_utc_datetime("2026-08-02T12:00:00Z") == datetime(
        2026, 8, 2, 12, 0, tzinfo=UTC
    )
    with pytest.raises(argparse.ArgumentTypeError):
        parse_utc_datetime("2026-08-02T15:00:00+03:00")


def test_cli_invokes_snapshot_with_explicit_policy_and_prints_allowlist(
    capsys,
) -> None:
    service = CapturingHealthService(ContentSupplyHealthSignal.NOMINAL)

    exit_code = main(
        [
            "--pending-dispatch-threshold",
            "11",
            "--queued-run-threshold",
            "12",
            "--unreviewed-proposal-threshold",
            "13",
            "--recent-non-success-threshold",
            "2",
            "--max-cycle-silence-seconds",
            "600",
            "--failure-window-seconds",
            "7200",
            "--as-of",
            "2026-08-02T12:00:00Z",
        ],
        app_factory=_factory(service),
    )

    assert exit_code == 0
    assert len(service.calls) == 1
    policy, as_of = service.calls[0]
    assert policy.pending_dispatch_attention_threshold == 11
    assert policy.queued_run_attention_threshold == 12
    assert policy.unreviewed_proposal_attention_threshold == 13
    assert policy.recent_non_success_attention_threshold == 2
    assert policy.max_cycle_silence_seconds == 600
    assert policy.failure_window_seconds == 7200
    assert as_of == datetime(2026, 8, 2, 12, 0, tzinfo=UTC)
    output = json.loads(capsys.readouterr().out)
    assert output["signal"] == "NOMINAL"
    assert set(output) == {
        "signal",
        "as_of",
        "reason_codes",
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
        "latest_terminal_cycle_state",
        "latest_terminal_cycle_completed_at",
        "seconds_since_latest_terminal_cycle",
    }


def test_cli_exit_codes_are_deterministic() -> None:
    assert exit_code_for(ContentSupplyHealthSignal.QUIET) == 0
    assert exit_code_for(ContentSupplyHealthSignal.NOMINAL) == 0
    assert exit_code_for(ContentSupplyHealthSignal.ATTENTION) == 2
    assert exit_code_for(ContentSupplyHealthSignal.CRITICAL) == 3


def test_cli_invalid_policy_returns_usage_exit_without_service_call() -> None:
    service = CapturingHealthService(ContentSupplyHealthSignal.NOMINAL)

    exit_code = main(
        ["--pending-dispatch-threshold", "1000001"],
        app_factory=_factory(service),
    )

    assert exit_code == INVALID_INPUT_EXIT_CODE
    assert service.calls == []
