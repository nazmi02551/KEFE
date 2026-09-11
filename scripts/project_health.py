#!/usr/bin/env python3
"""Run truthful, repeatable KEFE local health profiles.

The default profile exercises every local, provider-independent gate that can
be reproduced from a clean checkout. It deliberately does not claim PostgreSQL,
external-provider, device, store, deployment, or human-review evidence.

Use ``--quick`` while iterating and the default full profile before handoff.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Check:
    name: str
    command: tuple[str, ...]
    cwd: Path = ROOT
    environment: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


def _resolved_command(command: Sequence[str]) -> list[str]:
    """Resolve command shims (notably npm.cmd on Windows) without a shell."""

    resolved = list(command)
    executable = shutil.which(resolved[0])
    if executable:
        resolved[0] = executable
    return resolved


def _tail(text: str, *, limit: int = 1200) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[-limit:]


def run_check(check: Check) -> CheckResult:
    print(f"\n[+] {check.name}")
    print(f"    cwd: {check.cwd}")
    print(f"    cmd: {' '.join(check.command)}")
    environment = os.environ.copy()
    environment.update(dict(check.environment))
    try:
        completed = subprocess.run(
            _resolved_command(check.command),
            cwd=str(check.cwd),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
    except (OSError, ValueError) as error:
        detail = f"could not start: {error}"
        print(f"    FAIL: {detail}")
        return CheckResult(check.name, False, detail)

    combined = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
    detail = _tail(combined)
    if completed.returncode == 0:
        print("    PASS")
        if detail:
            print(f"    {_tail(detail, limit=300)}")
        return CheckResult(check.name, True, detail)

    print(f"    FAIL (exit {completed.returncode})")
    if detail:
        print(detail)
    return CheckResult(check.name, False, detail)


def git_clean_check() -> CheckResult:
    check = Check("Git worktree clean", ("git", "status", "--porcelain"))
    print(f"\n[+] {check.name}")
    try:
        completed = subprocess.run(
            _resolved_command(check.command),
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
    except (OSError, ValueError) as error:
        detail = f"could not start: {error}"
        print(f"    FAIL: {detail}")
        return CheckResult(check.name, False, detail)

    dirty = completed.stdout.strip()
    if completed.returncode == 0 and not dirty:
        print("    PASS")
        return CheckResult(check.name, True)

    detail = dirty or completed.stderr.strip() or f"git exited {completed.returncode}"
    print("    FAIL: tracked or untracked changes are present")
    if detail:
        print(_tail(detail))
    return CheckResult(check.name, False, detail)


def validator_checks() -> list[Check]:
    return [
        Check(
            f"Validator: {path.stem.removeprefix('validate_').replace('_', ' ')}",
            (sys.executable, str(path)),
        )
        for path in sorted((ROOT / "scripts").glob("validate_*.py"))
    ]


def package_checks() -> list[Check]:
    return [
        Check(
            "Package: design tokens",
            ("node", "packages/kefe-design-tokens/scripts/validate.mjs"),
        ),
        Check("Package: locale", ("node", "packages/kefe-locale/scripts/validate.mjs")),
        Check(
            "Package: test fixtures",
            ("node", "packages/kefe-test-fixtures/scripts/validate.mjs"),
        ),
    ]


def quick_checks() -> list[Check]:
    api = ROOT / "services" / "api"
    admin = ROOT / "apps" / "admin"
    web = ROOT / "apps" / "web"
    mobile = ROOT / "apps" / "mobile"
    return [
        *validator_checks(),
        Check("API lint", (sys.executable, "-m", "ruff", "check", "."), api),
        Check("Admin contracts", ("npm", "run", "contract"), admin),
        Check("Admin lint", ("npm", "run", "lint"), admin),
        Check("Admin typecheck", ("npm", "run", "typecheck"), admin),
        Check("Admin tests", ("npm", "test"), admin),
        Check("Web lint", ("npm", "run", "lint"), web),
        Check("Web typecheck", ("npm", "run", "typecheck"), web),
        Check("Web tests", ("npm", "test"), web),
        *package_checks(),
        Check("Mobile analyze", ("flutter", "analyze"), mobile),
    ]


def full_checks(*, include_postgres: bool) -> list[Check]:
    api = ROOT / "services" / "api"
    admin = ROOT / "apps" / "admin"
    web = ROOT / "apps" / "web"
    mobile = ROOT / "apps" / "mobile"
    checks = [
        *validator_checks(),
        Check("API lint", (sys.executable, "-m", "ruff", "check", "."), api),
        Check("API full in-memory tests", (sys.executable, "-m", "pytest", "-q"), api),
        Check("Admin full verify", ("npm", "run", "verify"), admin),
        Check("Web full verify", ("npm", "run", "verify"), web),
        *package_checks(),
        Check("Mobile analyze", ("flutter", "analyze"), mobile),
        Check("Mobile full tests", ("flutter", "test", "--concurrency=1"), mobile),
    ]
    if include_postgres:
        checks.append(
            Check(
                "API PostgreSQL tests",
                (sys.executable, "-m", "pytest", "-q"),
                api,
                (("KEFE_PERSISTENCE_BACKEND", "postgres"),),
            )
        )
    return checks


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run static, contract and lightweight test gates; do not claim full local health.",
    )
    parser.add_argument(
        "--include-postgres",
        action="store_true",
        help="Also run the API suite with KEFE_PERSISTENCE_BACKEND=postgres.",
    )
    parser.add_argument(
        "--skip-git-clean",
        action="store_true",
        help="Do not require a clean worktree (useful only during local iteration).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.quick and args.include_postgres:
        print("--include-postgres is available only in the full profile.", file=sys.stderr)
        return 2

    profile = "QUICK" if args.quick else "FULL LOCAL"
    print("=" * 72)
    print(f"KEFE PROJECT HEALTH — {profile} PROFILE")
    print("=" * 72)

    checks = quick_checks() if args.quick else full_checks(include_postgres=args.include_postgres)
    results = [run_check(check) for check in checks]
    if not args.skip_git_clean:
        results.append(git_clean_check())

    print("\n" + "=" * 72)
    print("RESULTS")
    print("=" * 72)
    for result in results:
        print(f"{'PASS' if result.passed else 'FAIL':<4}  {result.name}")

    failures = [result for result in results if not result.passed]
    print("=" * 72)
    if failures:
        print(f"FAILED: {len(failures)} of {len(results)} checks failed.")
        return 1

    if args.quick:
        print("QUICK PROFILE PASSED. Full local health was not established.")
    else:
        exclusions = ["external providers", "device/store", "deployment", "human review"]
        if not args.include_postgres:
            exclusions.insert(0, "PostgreSQL")
        print("FULL LOCAL PROFILE PASSED.")
        print("Not established by this run: " + ", ".join(exclusions) + ".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
