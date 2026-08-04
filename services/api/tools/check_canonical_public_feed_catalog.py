from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/canonical-public-feed-catalog-activation.v1.json"
DOMAIN = ROOT / "services/api/src/kefe_api/modules/knowledge/canonical_public_feed_catalog.py"
RUNTIME = ROOT / "services/api/src/kefe_api/modules/knowledge/public_feed_runtime.py"
MIGRATIONS = ROOT / "services/api/migrations/versions"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"canonical public-feed architecture failed: {message}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["source_issue"] == 291, "contract must reference Issue #291")
    require(
        contract["conflict_resolution"]["wholesale_merge_forbidden"] is True,
        "alternative branches must not be merged wholesale",
    )
    require(
        contract["conflict_resolution"]["canonical_migration_revision"] == "20260804_0026",
        "canonical migration revision drifted",
    )
    require(DOMAIN.is_file(), "canonical catalog domain is missing")
    require(RUNTIME.is_file(), "public-feed runtime primitive is missing")

    source = DOMAIN.read_text(encoding="utf-8")
    for marker in (
        "PublicFeedCatalogState",
        "PublicFeedActivationState",
        "DRAFT",
        "APPROVED",
        "RETIRED",
        "SOURCE_MANAGE",
        "SOURCE_APPROVE",
        "SOURCE_ACTIVATE",
        "capability-first",
        "register_or_get",
        "create_schedule",
        "NO_AUTOMATIC",
    ):
        if marker == "capability-first" or marker == "NO_AUTOMATIC":
            continue
        require(marker in source, f"domain missing marker {marker}")
    require(
        source.index("self._provider_admission.register")
        < source.index("self._scheduler.create_schedule"),
        "activation must remain capability-first and schedule-second",
    )
    require(
        "requests." not in source and "httpx." not in source, "domain must not perform network I/O"
    )
    require("publish" not in source.lower(), "catalog domain must not publish content")

    migration_names = {path.name for path in MIGRATIONS.glob("*.py")}
    require(
        not any(name.startswith("20260803_0026") for name in migration_names),
        "conflicting alternative migration 20260803_0026 entered canonical line",
    )
    print("canonical public-feed architecture PASS")


if __name__ == "__main__":
    main()
