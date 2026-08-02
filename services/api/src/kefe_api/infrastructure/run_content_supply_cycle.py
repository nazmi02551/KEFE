from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from typing import Protocol

from kefe_api.modules.content_supply_cycle.models import (
    ContentSupplyCycleCommand,
    ContentSupplyPipelineTarget,
)
from kefe_api.modules.content_supply_cycle.service import (
    ContentSupplyCycleOutcome,
    ContentSupplyCycleResult,
)

INVALID_INPUT_EXIT_CODE = 64


class ContentSupplyCycleRunner(Protocol):
    def run_once(self, command: ContentSupplyCycleCommand) -> ContentSupplyCycleResult: ...


class ApplicationState(Protocol):
    content_supply_cycle_service: ContentSupplyCycleRunner


class Application(Protocol):
    state: ApplicationState


def _default_app_factory() -> Application:
    from kefe_api.main import create_app

    return create_app()


def parse_pipeline_target(value: str) -> ContentSupplyPipelineTarget:
    try:
        identity, raw_max_runs = value.rsplit(":", 1)
        pipeline_code, pipeline_version = identity.rsplit("@", 1)
        max_runs = int(raw_max_runs)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(
            "pipeline target must use PIPELINE_CODE@PIPELINE_VERSION:MAX_RUNS"
        ) from exc
    try:
        return ContentSupplyPipelineTarget(
            pipeline_code=pipeline_code,
            pipeline_version=pipeline_version,
            max_runs=max_runs,
        )
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kefe-content-supply-cycle",
        description="Run one bounded KEFE content-supply process cycle.",
    )
    parser.add_argument("--worker-ref", required=True)
    parser.add_argument("--plan-budget", type=int, default=10)
    parser.add_argument("--dispatch-budget", type=int, default=10)
    parser.add_argument("--cycle-ttl-seconds", type=int, default=300)
    parser.add_argument("--dispatch-ttl-seconds", type=int, default=120)
    parser.add_argument("--ingestion-ttl-seconds", type=int, default=120)
    parser.add_argument(
        "--pipeline",
        action="append",
        type=parse_pipeline_target,
        default=[],
        metavar="CODE@VERSION:MAX_RUNS",
    )
    return parser


def exit_code_for(outcome: ContentSupplyCycleOutcome) -> int:
    if outcome in {
        ContentSupplyCycleOutcome.IDLE,
        ContentSupplyCycleOutcome.SUCCEEDED,
    }:
        return 0
    if outcome is ContentSupplyCycleOutcome.DEGRADED:
        return 2
    return 3


def main(
    argv: Sequence[str] | None = None,
    *,
    app_factory: Callable[[], Application] = _default_app_factory,
) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        command = ContentSupplyCycleCommand(
            worker_ref=args.worker_ref,
            plan_budget=args.plan_budget,
            dispatch_budget=args.dispatch_budget,
            pipeline_targets=tuple(args.pipeline),
            cycle_ttl_seconds=args.cycle_ttl_seconds,
            dispatch_ttl_seconds=args.dispatch_ttl_seconds,
            ingestion_ttl_seconds=args.ingestion_ttl_seconds,
        )
    except SystemExit as exc:
        return 0 if exc.code == 0 else INVALID_INPUT_EXIT_CODE
    except ValueError as exc:
        parser.print_usage()
        print(f"{parser.prog}: error: {exc}")
        return INVALID_INPUT_EXIT_CODE

    app = app_factory()
    result = app.state.content_supply_cycle_service.run_once(command)
    print(json.dumps(result.as_operational_dict(), sort_keys=True))
    return exit_code_for(result.outcome)


if __name__ == "__main__":
    raise SystemExit(main())
