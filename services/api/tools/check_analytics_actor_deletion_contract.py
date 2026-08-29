from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = (
    ROOT / "docs/contracts/analytics-actor-deletion-anonymization.v1.json"
)
PARENT_CONTRACT_PATH = (
    ROOT / "docs/contracts/privacy-export-deletion-hardening.v1.json"
)
ADR_PATH = (
    ROOT / "docs/adr/0136-self-service-deletion-of-retained-analytics-identity.md"
)
MEMORY_ANALYTICS_PATH = (
    ROOT / "services/api/src/kefe_api/modules/analytics/in_memory.py"
)
MEMORY_PRIVACY_PATH = (
    ROOT / "services/api/src/kefe_api/modules/privacy/in_memory.py"
)
POSTGRES_PRIVACY_PATH = (
    ROOT / "services/api/src/kefe_api/infrastructure/postgres_privacy.py"
)
MIGRATION_PATH = (
    ROOT
    / "services/api/migrations/versions/20260829_0040_analytics_actor_deletion_anonymization.py"
)
MEMORY_TEST_PATH = (
    ROOT / "services/api/tests/test_privacy_export_deletion_hardening.py"
)
POSTGRES_TEST_PATH = (
    ROOT / "services/api/tests/test_privacy_export_deletion_hardening_postgres.py"
)
SCHEMA_CONTRACT_PATH = (
    ROOT / "docs/contracts/connected-alpha-schema-snapshot.v1.json"
)


def _require(source: str, fragments: tuple[str, ...], label: str) -> list[str]:
    return [
        f"{label} missing: {fragment}"
        for fragment in fragments
        if fragment not in source
    ]


def main() -> int:
    errors: list[str] = []
    paths = (
        CONTRACT_PATH,
        PARENT_CONTRACT_PATH,
        ADR_PATH,
        MEMORY_ANALYTICS_PATH,
        MEMORY_PRIVACY_PATH,
        POSTGRES_PRIVACY_PATH,
        MIGRATION_PATH,
        MEMORY_TEST_PATH,
        POSTGRES_TEST_PATH,
        SCHEMA_CONTRACT_PATH,
    )
    for path in paths:
        if not path.exists():
            errors.append(f"missing required path: {path.relative_to(ROOT)}")
    if errors:
        print("\n".join(errors))
        return 1

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    parent = json.loads(PARENT_CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_CONTRACT_PATH.read_text(encoding="utf-8"))

    if contract.get("issue") != 383:
        errors.append("analytics actor deletion issue must be #383")
    if contract.get("capabilities") != ["CAP-085", "CAP-115"]:
        errors.append("analytics actor deletion capability scope changed")
    if contract.get("lifecycle_promotion") is not False:
        errors.append("analytics actor deletion must not promote lifecycle")

    expected_inventory = {
        ("analytics.analytics_event", "actor_id", "SET_NULL", "RETAIN"),
        ("analytics.activation_journey", "actor_id", "SET_NULL", "RETAIN"),
    }
    inventory = {
        (
            item.get("table"),
            item.get("column"),
            item.get("deletion_action"),
            item.get("row_action"),
        )
        for item in contract.get("retained_actor_reference_inventory", [])
    }
    if inventory != expected_inventory:
        errors.append(f"retained analytics actor inventory changed: {sorted(inventory)}")

    deletion = contract.get("deletion", {})
    for key in (
        "postgres_same_transaction",
        "memory_same_deletion_lock",
        "existing_receipt_repairs_before_return",
        "existing_receipt_identity_preserved",
        "future_table_auto_claim_forbidden",
        "catalog_drift_must_fail_contract",
    ):
        if deletion.get(key) is not True:
            errors.append(f"deletion boundary must require {key}")

    surface = contract.get("surface", {})
    if any(surface.get(key) is not False for key in surface):
        errors.append("analytics deletion repair must expose no new surface")

    extension = {
        item.get("issue"): item.get("contract")
        for item in parent.get("extensions", [])
    }
    if extension.get(383) != (
        "docs/contracts/analytics-actor-deletion-anonymization.v1.json"
    ):
        errors.append("parent privacy contract must name the #383 extension")
    retained = set(parent.get("deletion_coverage", {}).get(
        "retained_audit_anonymization", []
    ))
    if not {
        "analytics.analytics_event.actor_id_set_null",
        "analytics.activation_journey.actor_id_set_null",
    }.issubset(retained):
        errors.append("parent privacy coverage lacks retained analytics columns")

    memory_analytics = MEMORY_ANALYTICS_PATH.read_text(encoding="utf-8")
    errors.extend(
        _require(
            memory_analytics,
            (
                "def anonymize_actor(self, actor_id: UUID)",
                "replace(event, actor_id=None)",
                "replace(journey, actor_id=None)",
            ),
            "memory analytics anonymizer",
        )
    )
    memory_privacy = MEMORY_PRIVACY_PATH.read_text(encoding="utf-8")
    if memory_privacy.count("self._analytics.anonymize_actor(actor_id)") != 2:
        errors.append("memory deletion and receipt replay must both anonymize analytics")

    postgres_privacy = POSTGRES_PRIVACY_PATH.read_text(encoding="utf-8")
    errors.extend(
        _require(
            postgres_privacy,
            (
                "self._anonymize_analytics_actor(connection, actor_id)",
                "UPDATE analytics.analytics_event",
                "UPDATE analytics.activation_journey",
                "SET actor_id = NULL WHERE actor_id = :actor_id",
            ),
            "PostgreSQL privacy transaction",
        )
    )
    if "DELETE FROM analytics.analytics_event" in postgres_privacy:
        errors.append("privacy deletion must retain analytics event rows")
    if "DELETE FROM analytics.activation_journey" in postgres_privacy:
        errors.append("privacy deletion must retain activation journey rows")

    migration = MIGRATION_PATH.read_text(encoding="utf-8")
    errors.extend(
        _require(
            migration,
            (
                'revision = "20260829_0040"',
                'down_revision = "20260829_0039"',
                "WHERE state = 'DELETED'",
                "privacy.actor_deletion_receipt",
                "UPDATE analytics.analytics_event AS event",
                "UPDATE analytics.activation_journey AS journey",
                "SET actor_id = NULL",
                "Actor references are deliberately not reconstructed",
            ),
            "historical anonymization migration",
        )
    )
    if "DELETE FROM analytics." in migration:
        errors.append("migration must not delete retained analytics rows")

    memory_tests = MEMORY_TEST_PATH.read_text(encoding="utf-8")
    postgres_tests = POSTGRES_TEST_PATH.read_text(encoding="utf-8")
    errors.extend(
        _require(
            memory_tests,
            (
                "test_memory_deletion_anonymizes_retained_analytics_and_replay_repairs",
                "analytics_event_store",
            ),
            "memory deletion tests",
        )
    )
    errors.extend(
        _require(
            postgres_tests,
            (
                "EXPECTED_RETAINED_ANALYTICS_ACTOR_COLUMNS",
                "test_postgres_retained_analytics_actor_column_catalog_is_explicit",
                "test_postgres_0040_backfills_preexisting_deleted_actor_references",
                "analytics.activation_journey",
                "analytics.analytics_event",
            ),
            "PostgreSQL deletion tests",
        )
    )

    canonical = schema.get("canonical_chain", {})
    if canonical.get("expected_head") != "20260829_0040":
        errors.append("schema snapshot head must be 20260829_0040")
    if canonical.get("expected_migration_file_count") != 40:
        errors.append("schema snapshot migration count must be 40")

    if errors:
        print("Analytics actor deletion contract check FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Analytics actor deletion contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
