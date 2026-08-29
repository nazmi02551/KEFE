from __future__ import annotations

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs/contracts/quality-journey-projection.v1.json"
ADR = REPO_ROOT / "docs/adr/0137-reproducible-session-quality-journey.md"
MODELS = REPO_ROOT / "services/api/src/kefe_api/modules/analytics/models.py"
SERVICE = REPO_ROOT / "services/api/src/kefe_api/modules/analytics/service.py"
MEMORY = REPO_ROOT / "services/api/src/kefe_api/modules/analytics/in_memory.py"
POSTGRES = REPO_ROOT / "services/api/src/kefe_api/infrastructure/postgres_analytics.py"
MIGRATION = (
    REPO_ROOT / "services/api/migrations/versions/20260829_0041_quality_journey_projection.py"
)
MEMORY_TEST = REPO_ROOT / "services/api/tests/test_quality_journey_projection.py"
POSTGRES_TEST = REPO_ROOT / "services/api/tests/test_quality_journey_postgres.py"
OPENAPI = REPO_ROOT / "docs/contracts/openapi.v1.json"


def _require(content: str, fragments: tuple[str, ...], *, label: str) -> list[str]:
    return [f"{label} missing: {fragment}" for fragment in fragments if fragment not in content]


def _quality_journey_fields(source: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "QualityJourney":
            return {
                child.target.id
                for child in node.body
                if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name)
            }
    return set()


def main() -> int:
    errors: list[str] = []
    paths = (
        CONTRACT,
        ADR,
        MODELS,
        SERVICE,
        MEMORY,
        POSTGRES,
        MIGRATION,
        MEMORY_TEST,
        POSTGRES_TEST,
        OPENAPI,
    )
    for path in paths:
        if not path.exists():
            errors.append(f"missing required path: {path.relative_to(REPO_ROOT)}")
    if errors:
        print("\n".join(errors))
        return 1

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("issue") != 385:
        errors.append("quality journey issue must be #385")
    if contract.get("capabilities") != ["CAP-116"]:
        errors.append("quality journey must remain scoped to CAP-116")

    expected_stages = {
        ("activation.weigh_committed", 1),
        ("quality.perspective_viewed", 1),
        ("quality.exposure_recorded", 1),
        ("quality.intervention_exposed", 1),
        ("quality.decision_revised", 1),
    }
    stages = {
        (item.get("analytics_name"), item.get("analytics_version"))
        for item in contract.get("stages", [])
    }
    if stages != expected_stages:
        errors.append(f"quality journey stage mismatch: {sorted(stages)}")

    identity = contract.get("identity", {})
    if identity.get("actor_id_stored") is not False:
        errors.append("quality journey must not store actor identity")
    if identity.get("event_payload_copied") is not False:
        errors.append("quality journey must not copy event payload")
    if identity.get("non_null_case_version_values_must_agree") is not True:
        errors.append("non-null CaseVersion consistency must be explicit")
    if identity.get("conflict_behavior") != "FAIL_CLOSED_ATOMIC_ROLLBACK":
        errors.append("quality provenance conflict must fail closed")

    reconstruction = contract.get("reconstruction", {})
    if reconstruction.get("order_independent") is not True:
        errors.append("quality journey must be order independent")
    if reconstruction.get("same_stage_selection") != ("MIN_OCCURRED_AT_THEN_SOURCE_EVENT_ID"):
        errors.append("same-stage selection must be deterministic")
    if reconstruction.get("missing_stage_behavior") != "PRESERVE_NULL":
        errors.append("missing quality stages must remain null")

    persistence = contract.get("persistence", {})
    for key in (
        "event_and_journey_same_operation",
        "activation_and_quality_projection_same_transaction",
        "postgres_same_transaction",
        "postgres_session_scoped_serialization",
        "migration_backfills_existing_events",
    ):
        if persistence.get(key) is not True:
            errors.append(f"quality journey persistence must require {key}")
    if persistence.get("backfill_conflict_behavior") != ("FAIL_CLOSED_MIGRATION_ABORT"):
        errors.append("quality backfill conflict must fail closed")

    surface = contract.get("surface", {})
    if any(surface.get(key) is not False for key in surface):
        errors.append("quality journey must remain an internal non-aggregate surface")

    model_source = MODELS.read_text(encoding="utf-8")
    fields = _quality_journey_fields(model_source)
    required_fields = {
        "session_id",
        "case_version_id",
        "committed_at",
        "committed_source_event_id",
        "perspective_viewed_at",
        "perspective_viewed_source_event_id",
        "exposure_recorded_at",
        "exposure_recorded_source_event_id",
        "intervention_exposed_at",
        "intervention_exposed_source_event_id",
        "decision_revised_at",
        "decision_revised_source_event_id",
    }
    if fields != required_fields:
        errors.append(f"quality journey fields changed: {sorted(fields)}")
    if fields & {"actor_id", "payload", "score", "cohort"}:
        errors.append("quality journey contains forbidden identity/claim fields")

    service_source = SERVICE.read_text(encoding="utf-8")
    errors.extend(
        _require(
            service_source,
            (
                "class QualityJourneyProjector:",
                "class QualityJourneyProjectionError",
                "quality session_id conflict",
                "quality case_version_id conflict",
                "def rebuild(",
                "candidate_source_event_id",
            ),
            label="quality journey runtime",
        )
    )

    memory_source = MEMORY.read_text(encoding="utf-8")
    errors.extend(
        _require(
            memory_source,
            (
                "self._quality_journeys",
                "self._quality_journey_projector.apply",
                "def get_quality_journey",
            ),
            label="memory quality journey adapter",
        )
    )

    postgres_source = POSTGRES.read_text(encoding="utf-8")
    errors.extend(
        _require(
            postgres_source,
            (
                "pg_advisory_xact_lock",
                "INSERT INTO analytics.quality_journey",
                "ON CONFLICT (session_id) DO UPDATE",
                "def get_quality_journey",
                "FROM analytics.quality_journey",
            ),
            label="PostgreSQL quality journey adapter",
        )
    )

    migration_source = MIGRATION.read_text(encoding="utf-8")
    errors.extend(
        _require(
            migration_source,
            (
                'revision = "20260829_0041"',
                'down_revision = "20260829_0040"',
                "CREATE TABLE analytics.quality_journey",
                "session_id uuid PRIMARY KEY",
                "quality journey backfill found conflicting CaseVersion provenance",
                "count(DISTINCT case_version_id) > 1",
                "ORDER BY session_id, occurred_at, source_event_id",
                "DROP TABLE IF EXISTS analytics.quality_journey",
            ),
            label="quality journey migration",
        )
    )
    if "actor_id" in migration_source:
        errors.append("quality journey migration must not store actor identity")
    if "DROP SCHEMA" in migration_source:
        errors.append("quality journey migration must preserve the shared schema")

    openapi_source = OPENAPI.read_text(encoding="utf-8")
    if "quality_journey" in openapi_source:
        errors.append("quality journey must not leak into public OpenAPI")

    if errors:
        print("Quality journey contract check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Quality journey contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
