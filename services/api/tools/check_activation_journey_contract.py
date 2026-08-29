from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "activation-journey-projection.v1.json"
)
ADR = (
    REPO_ROOT
    / "docs"
    / "adr"
    / "0135-reproducible-session-activation-journey.md"
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
    / "20260829_0039_activation_journey_projection.py"
)
OPENAPI = REPO_ROOT / "docs" / "contracts" / "openapi.v1.json"


def _require(content: str, fragments: tuple[str, ...], *, label: str) -> list[str]:
    return [
        f"{label} missing: {fragment}"
        for fragment in fragments
        if fragment not in content
    ]


def main() -> int:
    errors: list[str] = []
    required_paths = (CONTRACT, ADR, ANALYTICS, POSTGRES, MIGRATION, OPENAPI)
    for path in required_paths:
        if not path.exists():
            errors.append(f"missing required path: {path.relative_to(REPO_ROOT)}")
    if errors:
        print("\n".join(errors))
        return 1

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("issue") != 380:
        errors.append("activation journey issue must be #380")
    if contract.get("capabilities") != ["CAP-115"]:
        errors.append("activation journey must remain scoped to CAP-115")

    expected_stages = {
        ("activation.weigh_started", 1),
        ("activation.weigh_committed", 1),
        ("activation.result_revealed", 1),
    }
    stages = {
        (item.get("analytics_name"), item.get("analytics_version"))
        for item in contract.get("stages", [])
    }
    if stages != expected_stages:
        errors.append(f"activation journey stage mismatch: {sorted(stages)}")

    reconstruction = contract.get("reconstruction", {})
    if reconstruction.get("order_independent") is not True:
        errors.append("activation journey must be order independent")
    if reconstruction.get("same_stage_selection") != (
        "MIN_OCCURRED_AT_THEN_SOURCE_EVENT_ID"
    ):
        errors.append("same-stage selection must be deterministic")
    if reconstruction.get("missing_stage_behavior") != "PRESERVE_NULL":
        errors.append("missing activation stages must remain null")

    identity = contract.get("identity", {})
    if identity.get("conflict_behavior") != "FAIL_CLOSED_ATOMIC_ROLLBACK":
        errors.append("activation provenance conflict must fail closed")
    if identity.get("required_consistency") != ["session_id", "case_version_id"]:
        errors.append("session and CaseVersion consistency must remain explicit")

    persistence = contract.get("persistence", {})
    if persistence.get("migration_backfills_existing_events") is not True:
        errors.append("migration must backfill existing activation facts")
    if persistence.get("backfill_conflict_behavior") != (
        "FAIL_CLOSED_MIGRATION_ABORT"
    ):
        errors.append("migration backfill provenance conflict must fail closed")

    surface = contract.get("surface", {})
    if any(surface.get(key) is not False for key in surface):
        errors.append("activation journey must remain an internal non-aggregate surface")

    source = "\n".join(
        path.read_text(encoding="utf-8") for path in ANALYTICS.glob("*.py")
    )
    errors.extend(
        _require(
            source,
            (
                "class ActivationJourney:",
                "class ActivationJourneyProjector:",
                "started_source_event_id",
                "committed_source_event_id",
                "result_revealed_source_event_id",
                "activation actor_id conflict",
                "activation case_version_id conflict",
                "def rebuild(",
            ),
            label="activation journey runtime",
        )
    )
    if "from fastapi" in source:
        errors.append("HTTP framework leaked into analytics domain")

    postgres_source = POSTGRES.read_text(encoding="utf-8")
    errors.extend(
        _require(
            postgres_source,
            (
                "pg_advisory_xact_lock",
                "hashtextextended",
                "INSERT INTO analytics.activation_journey",
                "ON CONFLICT (session_id) DO UPDATE",
                "get_activation_journey",
                "list_by_session",
            ),
            label="PostgreSQL activation journey adapter",
        )
    )

    migration_source = MIGRATION.read_text(encoding="utf-8")
    errors.extend(
        _require(
            migration_source,
            (
                'revision = "20260829_0039"',
                'down_revision = "20260829_0038"',
                "CREATE TABLE analytics.activation_journey",
                "session_id uuid PRIMARY KEY",
                "case_version_id uuid NOT NULL",
                "activation journey backfill found conflicting provenance",
                "count(DISTINCT case_version_id) <> 1",
                "count(DISTINCT actor_id) > 1",
                "ORDER BY session_id, occurred_at, source_event_id",
                "DROP TABLE IF EXISTS analytics.activation_journey",
            ),
            label="activation journey migration",
        )
    )
    if "DROP SCHEMA" in migration_source:
        errors.append("activation journey migration must preserve the shared schema")

    openapi_source = OPENAPI.read_text(encoding="utf-8")
    if "activation_journey" in openapi_source:
        errors.append("activation journey must not leak into public OpenAPI")

    if errors:
        print("Activation journey contract check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Activation journey contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
