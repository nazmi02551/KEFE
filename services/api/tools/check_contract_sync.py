from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
API_SRC = REPO_ROOT / "services" / "api" / "src"
CONTRACTS = REPO_ROOT / "docs" / "contracts"


def _registered_error_codes() -> set[str]:
    content = (CONTRACTS / "error-codes.v1.yaml").read_text(encoding="utf-8")
    return set(re.findall(r"^- code: ([A-Z0-9_]+)$", content, flags=re.MULTILINE))


def _used_domain_error_codes() -> set[str]:
    codes: set[str] = set()
    pattern = re.compile(r'DomainError\(\s*"([A-Z0-9_]+)"')
    for path in API_SRC.rglob("*.py"):
        codes.update(pattern.findall(path.read_text(encoding="utf-8")))
    return codes


def _check_manifest_paths() -> list[str]:
    manifest = (CONTRACTS / "manifest.v1.yaml").read_text(encoding="utf-8")
    paths = re.findall(r"^\s*path: ([^\n]+)$", manifest, flags=re.MULTILINE)
    return [path for path in paths if not (REPO_ROOT / path.strip()).exists()]


def main() -> None:
    registered = _registered_error_codes()
    used = _used_domain_error_codes()
    missing_errors = sorted(used - registered)
    missing_paths = _check_manifest_paths()

    schema = (CONTRACTS / "postgresql-m0-schema.v1.0.1.sql").read_text(encoding="utf-8")
    schema_errors: list[str] = []
    if "commit_idempotency_key text" not in schema:
        schema_errors.append("M0 schema must expose explicit commit_idempotency_key")
    if "commit_idempotency_actor_key_idx" not in schema:
        schema_errors.append("M0 schema must enforce actor-scoped commit idempotency")
    if "outbox_decision_lifecycle_once_idx" not in schema:
        schema_errors.append("M0 schema must enforce lifecycle outbox uniqueness")

    problems: list[str] = []
    if missing_errors:
        problems.append(f"Unregistered DomainError codes: {', '.join(missing_errors)}")
    if missing_paths:
        problems.append(f"Missing contract manifest paths: {', '.join(missing_paths)}")
    problems.extend(schema_errors)

    if problems:
        raise SystemExit("\n".join(problems))

    print(
        "Contract sync OK: "
        f"{len(used)} executable DomainError codes registered; "
        "manifest paths and M0 persistence invariants verified."
    )


if __name__ == "__main__":
    main()
