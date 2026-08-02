from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Protocol

from kefe_api.modules.content_supply_health.models import (
    ContentSupplyHealthPolicy,
    ContentSupplyHealthSignal,
    ContentSupplyHealthSnapshot,
)

INVALID_INPUT_EXIT_CODE = 64


class ContentSupplyHealthSnapshotter(Protocol):
    def snapshot(
        self,
        policy: ContentSupplyHealthPolicy,
        *,
        as_of=None,
    ) -> ContentSupplyHealthSnapshot: ...


class ApplicationState(Protocol):
    content_supply_health_service: ContentSupplyHealthSnapshotter


class Application(Protocol):
    state: ApplicationState


def _default_app_factory() -> Application:
    from kefe_api.main import create_app

    return create_app()


def parse_utc_datetime(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("as-of must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise argparse.ArgumentTypeError("as-of must be timezone-aware UTC")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kefe-content-supply-health",
        description="Read one privacy-safe KEFE content-supply health snapshot.",
    )
    parser.add_argument("--pending-dispatch-threshold", type=int, default=100)
    parser.add_argument("--queued-run-threshold", type=int, default=100)
    parser.add_argument("--unreviewed-proposal-threshold", type=int, default=100)
    parser.add_argument("--recent-non-success-threshold", type=int, default=0)
    parser.add_argument("--max-cycle-silence-seconds", type=int, default=900)
    parser.add_argument("--failure-window-seconds", type=int, default=3600)
    parser.add_argument("--as-of", type=parse_utc_datetime)
    return parser


def exit_code_for(signal: ContentSupplyHealthSignal) -> int:
    if signal in {
        ContentSupplyHealthSignal.QUIET,
        ContentSupplyHealthSignal.NOMINAL,
    }:
        return 0
    if signal is ContentSupplyHealthSignal.ATTENTION:
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
        policy = ContentSupplyHealthPolicy(
            pending_dispatch_attention_threshold=args.pending_dispatch_threshold,
            queued_run_attention_threshold=args.queued_run_threshold,
            unreviewed_proposal_attention_threshold=(
                args.unreviewed_proposal_threshold
            ),
            recent_non_success_attention_threshold=(
                args.recent_non_success_threshold
            ),
            max_cycle_silence_seconds=args.max_cycle_silence_seconds,
            failure_window_seconds=args.failure_window_seconds,
        )
    except SystemExit as exc:
        return 0 if exc.code == 0 else INVALID_INPUT_EXIT_CODE
    except ValueError as exc:
        parser.print_usage()
        print(f"{parser.prog}: error: {exc}")
        return INVALID_INPUT_EXIT_CODE

    app = app_factory()
    snapshot = app.state.content_supply_health_service.snapshot(
        policy,
        as_of=args.as_of,
    )
    print(json.dumps(snapshot.as_operational_dict(), sort_keys=True))
    return exit_code_for(snapshot.signal)


if __name__ == "__main__":
    raise SystemExit(main())
