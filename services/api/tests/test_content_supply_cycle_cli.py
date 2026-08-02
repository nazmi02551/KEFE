from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from kefe_api.infrastructure.run_content_supply_cycle import (
    INVALID_INPUT_EXIT_CODE,
    exit_code_for,
    main,
    parse_pipeline_target,
)
from kefe_api.modules.content_supply_cycle.service import (
    ContentSupplyCycleOutcome,
    ContentSupplyCycleResult,
)


class CapturingCycleService:
    def __init__(self, outcome: ContentSupplyCycleOutcome) -> None:
        self.outcome = outcome
        self.commands = []

    def run_once(self, command):
        self.commands.append(command)
        return ContentSupplyCycleResult(
            outcome=self.outcome,
            cycle_id=uuid4(),
            worker_ref=command.worker_ref,
            plan_hash=command.plan_hash,
            planned_count=0,
            dispatch_attempted_count=0,
            dispatch_succeeded_count=0,
            dispatch_non_success_count=0,
            ingestion_attempted_count=0,
            ingestion_succeeded_count=0,
            ingestion_non_success_count=0,
            duration_ms=1,
            error_code=(
                "CONTENT_SUPPLY_DELEGATED_NON_SUCCESS"
                if self.outcome is ContentSupplyCycleOutcome.DEGRADED
                else None
            ),
        )


def _factory(service):
    return lambda: SimpleNamespace(
        state=SimpleNamespace(content_supply_cycle_service=service)
    )


def test_pipeline_target_parser_requires_exact_version_and_budget() -> None:
    target = parse_pipeline_target("NEWS_PIPELINE@1.2.0:7")

    assert target.pipeline_code == "NEWS_PIPELINE"
    assert target.pipeline_version == "1.2.0"
    assert target.max_runs == 7

    with pytest.raises(argparse.ArgumentTypeError):
        parse_pipeline_target("NEWS_PIPELINE:7")


def test_cli_invokes_exact_one_shot_command_and_prints_allowlist_json(
    capsys,
) -> None:
    service = CapturingCycleService(ContentSupplyCycleOutcome.SUCCEEDED)

    exit_code = main(
        [
            "--worker-ref",
            "cli-worker",
            "--plan-budget",
            "3",
            "--dispatch-budget",
            "4",
            "--cycle-ttl-seconds",
            "90",
            "--dispatch-ttl-seconds",
            "45",
            "--ingestion-ttl-seconds",
            "60",
            "--pipeline",
            "NEWS_PIPELINE@1.0.0:5",
        ],
        app_factory=_factory(service),
    )

    assert exit_code == 0
    assert len(service.commands) == 1
    command = service.commands[0]
    assert command.worker_ref == "cli-worker"
    assert command.plan_budget == 3
    assert command.dispatch_budget == 4
    assert command.pipeline_targets[0].identity == ("NEWS_PIPELINE", "1.0.0")
    assert command.pipeline_targets[0].max_runs == 5
    output = json.loads(capsys.readouterr().out)
    assert output["outcome"] == "SUCCEEDED"
    assert set(output) == {
        "outcome",
        "cycle_id",
        "worker_ref",
        "plan_hash",
        "planned_count",
        "dispatch_attempted_count",
        "dispatch_succeeded_count",
        "dispatch_non_success_count",
        "ingestion_attempted_count",
        "ingestion_succeeded_count",
        "ingestion_non_success_count",
        "duration_ms",
        "error_code",
    }


def test_cli_exit_codes_are_deterministic() -> None:
    assert exit_code_for(ContentSupplyCycleOutcome.IDLE) == 0
    assert exit_code_for(ContentSupplyCycleOutcome.SUCCEEDED) == 0
    assert exit_code_for(ContentSupplyCycleOutcome.DEGRADED) == 2
    assert exit_code_for(ContentSupplyCycleOutcome.FAILED) == 3
    assert exit_code_for(ContentSupplyCycleOutcome.LEASE_LOST) == 3


def test_cli_invalid_input_returns_usage_exit_without_running_service() -> None:
    service = CapturingCycleService(ContentSupplyCycleOutcome.SUCCEEDED)

    exit_code = main(
        ["--worker-ref", "cli-worker", "--plan-budget", "1000"],
        app_factory=_factory(service),
    )

    assert exit_code == INVALID_INPUT_EXIT_CODE
    assert service.commands == []
