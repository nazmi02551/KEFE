from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "analytics-event-spine-slice31.v1.json"
)
ADR = (
    REPO_ROOT
    / "docs"
    / "adr"
    / "0069-server-authoritative-analytics-event-spine.md"
)
ANALYTICS = (
    REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "analytics"
)
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_analytics.py"
)
MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260829_0038_analytics_event_spine.py"
)
WORKER = (
    REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "workers" / "outbox.py"
)


def _require(content: str, fragments: tuple[str, ...], *, label: str) -> list[str]:
    return [
        f"{label} missing: {fragment}"
        for fragment in fragments
        if fragment not in content
    ]


def main() -> int:
    errors: list[str] = []
    required_paths = (CONTRACT, ADR, ANALYTICS, POSTGRES, MIGRATION, WORKER)
    for path in required_paths:
        if not path.exists():
            errors.append(f"missing required path: {path.relative_to(REPO_ROOT)}")
    if errors:
        print("\n".join(errors))
        return 1

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("convergence_issue") != 378:
        errors.append("canonical analytics convergence issue must be #378")
    definitions = contract.get("definitions", [])
    names = {
        (item.get("source_event_name"), item.get("source_event_version"))
        for item in definitions
    }
    expected = {
        ("weigh.started", 1),
        ("weigh.committed", 1),
        ("result.revealed", 1),
        ("perspective.viewed", 1),
        ("exposure.recorded", 1),
        ("intervention.exposed", 1),
        ("decision.revised", 1),
    }
    if names != expected:
        errors.append(f"analytics source registry mismatch: {sorted(names)}")

    source_policy = contract.get("source_policy", {})
    if source_policy.get("server_authoritative_only") is not True:
        errors.append("server_authoritative_only must be true")
    if source_policy.get("client_ingestion_endpoint_in_scope") is not False:
        errors.append("client ingestion endpoint must remain excluded")

    convergence = contract.get("convergence", {})
    if convergence.get("source_exact_green_head") != (
        "ea041f18ccbf3bc10e5bec60f3bc07bb67301f99"
    ):
        errors.append("historical exact-green analytics source is not pinned")
    if convergence.get("canonical_parent_exact_green_head") != (
        "33c681cc00a73b2a405102336f6fe6a1fddd940c"
    ):
        errors.append("canonical convergence parent is not pinned")
    if convergence.get("selective_adoption_only") is not True:
        errors.append("analytics convergence must remain selective adoption")
    if convergence.get("historical_migration_replayed") is not False:
        errors.append("historical analytics migration must not be replayed")
    migration = convergence.get("migration", {})
    if migration != {
        "revision": "20260829_0038",
        "down_revision": "20260827_0037",
    }:
        errors.append("analytics convergence migration identity mismatch")

    forbidden = set(contract.get("forbidden_payload_keys", []))
    for required in {
        "responses",
        "private_reason",
        "reason_text",
        "reason_tags",
        "personality",
        "ideology",
        "psychometric",
        "bias",
        "causal_inference",
    }:
        if required not in forbidden:
            errors.append(f"forbidden payload key missing: {required}")

    source = "\n".join(
        path.read_text(encoding="utf-8") for path in ANALYTICS.glob("*.py")
    )
    errors.extend(
        _require(
            source,
            (
                "class AnalyticsEvent:",
                "class AnalyticsEventProjector:",
                "class AnalyticsProjectionTransport:",
                "class InMemoryAnalyticsEventStore:",
                "FORBIDDEN_PAYLOAD_KEYS",
                "CORE_PRE_RESULT",
                "ADVOCACY_SUPPORT",
                "uuid5(",
            ),
            label="analytics runtime",
        )
    )
    migration_source = MIGRATION.read_text(encoding="utf-8")
    errors.extend(
        _require(
            migration_source,
            (
                'revision = "20260829_0038"',
                'down_revision = "20260827_0037"',
                "CREATE SCHEMA IF NOT EXISTS analytics",
                "CREATE TABLE analytics.analytics_event",
                "UNIQUE(source_event_id, analytics_name, analytics_version)",
            ),
            label="analytics migration",
        )
    )
    if "DROP SCHEMA" in migration_source:
        errors.append("analytics migration must not drop the shared analytics schema")
    errors.extend(
        _require(
            WORKER.read_text(encoding="utf-8"),
            (
                "AnalyticsProjectionTransport",
                "PostgresAnalyticsEventStore",
                "CompositeEventTransport",
            ),
            label="outbox wiring",
        )
    )

    forbidden_provider_fragments = (
        "from amplitude",
        "import amplitude",
        "from mixpanel",
        "import mixpanel",
        "from segment",
        "import segment",
        "from firebase_admin",
        "import firebase_admin",
    )
    leaked = [fragment for fragment in forbidden_provider_fragments if fragment in source]
    if leaked:
        message = "analytics domain contains provider SDK dependency: "
        errors.append(message + ", ".join(leaked))
    if "from fastapi" in source:
        errors.append("HTTP framework leaked into analytics domain")

    if errors:
        print("Analytics event spine contract check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Analytics event spine contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
