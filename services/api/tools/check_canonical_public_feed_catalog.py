from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "docs/contracts/canonical-public-feed-catalog-activation.v1.json"
FEED_ITEM_CONTRACT = ROOT / "docs/contracts/feed-item-extraction-slice53.v1.json"
DOMAIN = ROOT / "services/api/src/kefe_api/modules/knowledge/canonical_public_feed_catalog.py"
RUNTIME = ROOT / "services/api/src/kefe_api/modules/knowledge/public_feed_runtime.py"
LIVE_RUNTIME = ROOT / "services/api/src/kefe_api/infrastructure/canonical_public_feed_runtime.py"
COMPOSITION = ROOT / "services/api/src/kefe_api/infrastructure/canonical_public_feed_composition.py"
PIPELINE = ROOT / "services/api/src/kefe_api/infrastructure/editorial_pipeline.py"
MAIN = ROOT / "services/api/src/kefe_api/main.py"
ROUTER = ROOT / "services/api/src/kefe_api/modules/admin_security/canonical_public_feed_router.py"
POSTGRES = (
    ROOT / "services/api/src/kefe_api/infrastructure/postgres_canonical_public_feed_catalog.py"
)
CANONICAL_MIGRATION = (
    ROOT / "services/api/migrations/versions/20260804_0026_canonical_public_feed_catalog.py"
)
HTTP_TEST = ROOT / "services/api/tests/test_canonical_public_feed_http.py"
VERTICAL_TEST = ROOT / "services/api/tests/test_canonical_public_feed_vertical.py"
POSTGRES_HTTP_TEST = ROOT / "services/api/tests/test_canonical_public_feed_http_postgres.py"
MIGRATIONS = ROOT / "services/api/migrations/versions"
TOOLS = ROOT / "services/api/tools"
COMPATIBILITY_CHECKERS = (
    TOOLS / "check_feed_item_extraction_contract.py",
    TOOLS / "check_ingestion_worker_runner_contract.py",
    TOOLS / "check_provider_admission_control_contract.py",
    TOOLS / "check_provider_http_capture_contract.py",
    TOOLS / "check_provider_http_transport_contract.py",
    TOOLS / "check_provider_pinned_runtime_contract.py",
    TOOLS / "check_public_provider_capture_contract.py",
    TOOLS / "check_rss_atom_public_capture_contract.py",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"canonical public-feed architecture failed: {message}")


def main() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    feed_item_contract = json.loads(FEED_ITEM_CONTRACT.read_text(encoding="utf-8"))
    require(contract["source_issue"] == 291, "contract must reference Issue #291")
    require(
        contract["conflict_resolution"]["wholesale_merge_forbidden"] is True,
        "alternative branches must not be merged wholesale",
    )
    require(
        contract["conflict_resolution"]["canonical_migration_revision"]
        == "20260804_0026",
        "canonical migration revision drifted",
    )
    require(
        feed_item_contract["version"] == "1.1.0",
        "feed item composition contract must include inert runtime adoption",
    )
    feed_composition = feed_item_contract["composition"]
    require(
        feed_composition["production_runtime_plans_registered"] == 1,
        "exactly one inert feed item plan must be installed",
    )
    require(
        feed_composition["production_processors_registered"] == 1,
        "exactly one deterministic feed item processor must be installed",
    )
    require(
        feed_composition["plan_registration_is_source_activation"] is False,
        "worker plan registration must remain distinct from source activation",
    )
    for field in (
        "seeded_feed_definitions",
        "seeded_provider_profiles",
        "seeded_public_adapters",
        "seeded_schedules",
        "concrete_providers_registered",
    ):
        require(feed_composition[field] == 0, f"{field} must remain zero")
    require(
        feed_composition["explicit_catalog_activation_required"] is True,
        "source runtime must require explicit catalog activation",
    )
    require(
        feed_composition["startup_network"] is False,
        "production startup must not perform feed network activity",
    )

    for path, label in (
        (DOMAIN, "canonical catalog domain"),
        (RUNTIME, "public-feed runtime primitive"),
        (LIVE_RUNTIME, "live public-feed runtime registry"),
        (COMPOSITION, "canonical public-feed composition"),
        (PIPELINE, "editorial pipeline"),
        (MAIN, "application composition"),
        (ROUTER, "Admin public-feed router"),
        (POSTGRES, "canonical PostgreSQL repository"),
        (CANONICAL_MIGRATION, "canonical migration"),
        (HTTP_TEST, "canonical Admin HTTP test"),
        (VERTICAL_TEST, "canonical vertical test"),
        (POSTGRES_HTTP_TEST, "canonical PostgreSQL HTTP test"),
        *tuple((path, f"compatibility checker {path.name}") for path in COMPATIBILITY_CHECKERS),
    ):
        require(path.is_file(), f"{label} is missing")

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
        "register_or_get",
        "create_schedule",
        "capability_template.instantiate",
        "definition.configuration_hash",
        "command.locale",
        "command.jurisdiction_code",
    ):
        require(marker in source, f"domain missing marker {marker}")
    require(
        source.index("self._provider_admission.register")
        < source.index("self._scheduler.create_schedule"),
        "activation must remain capability-first and schedule-second",
    )
    require(
        "requests." not in source and "httpx." not in source,
        "domain must not perform network I/O",
    )
    require("publish" not in source.lower(), "catalog domain must not publish content")

    for forbidden in (
        "definition.ingestion_configuration_hash",
        ".to_public_capability(",
        "command.context",
    ):
        require(
            forbidden not in source,
            f"legacy candidate API entered canonical domain: {forbidden}",
        )

    live_runtime_source = LIVE_RUNTIME.read_text(encoding="utf-8")
    for marker in (
        "MutableProviderAdoptionRegistry",
        "MutablePublicSourceCaptureRegistry",
        "CanonicalPublicFeedRuntimeProfileRegistry",
        "self._adapter_factory.create",
        "self._capture.register_or_get",
        "self._adoption.register_or_get",
    ):
        require(marker in live_runtime_source, f"live runtime missing {marker}")

    composition_source = COMPOSITION.read_text(encoding="utf-8")
    for marker in (
        "InMemoryPublicFeedCatalogRepository()",
        "PostgresCanonicalPublicFeedCatalogRepository",
        "CanonicalPublicFeedRuntimeProfileRegistry",
        "CanonicalPublicFeedCatalogService",
    ):
        require(marker in composition_source, f"composition missing {marker}")
    for forbidden in (
        "register_draft(",
        ".approve(",
        ".activate(",
        "create_schedule(",
    ):
        require(
            forbidden not in composition_source,
            f"startup composition must not execute {forbidden}",
        )

    pipeline_source = PIPELINE.read_text(encoding="utf-8")
    for marker in (
        "MutableProviderAdoptionRegistry()",
        "MutablePublicSourceCaptureRegistry()",
        "build_feed_item_extraction_runtime(",
        "FeedItemExtractionStageProcessor(",
    ):
        require(marker in pipeline_source, f"pipeline missing {marker}")

    checker_sources = {
        path.name: path.read_text(encoding="utf-8") for path in COMPATIBILITY_CHECKERS
    }
    combined_checkers = "\n".join(checker_sources.values())
    for forbidden in (
        "InMemoryProviderAdoptionRegistry()",
        "InMemoryPublicSourceCaptureRegistry()",
        "InMemoryIngestionWorkerRuntimeRegistry()",
    ):
        require(
            forbidden not in combined_checkers,
            f"legacy composition-only checker marker remains: {forbidden}",
        )
    for marker in (
        "MutableProviderAdoptionRegistry()",
        "MutablePublicSourceCaptureRegistry()",
        "build_feed_item_extraction_runtime(",
    ):
        require(marker in combined_checkers, f"canonical checker marker missing: {marker}")

    main_source = MAIN.read_text(encoding="utf-8")
    for marker in (
        "build_canonical_public_feed_composition(",
        "app.state.canonical_public_feed_repository",
        "app.state.canonical_public_feed_runtime_profiles",
        "app.state.canonical_public_feed_service",
        "_api_at_least(settings.api_version, 0, 24)",
        "app.include_router(admin_canonical_public_feed_router)",
    ):
        require(marker in main_source, f"main composition missing {marker}")

    router_source = ROUTER.read_text(encoding="utf-8")
    for marker in (
        "WritePrincipalDep",
        "ReadPrincipalDep",
        'router = APIRouter(prefix="/internal/admin/v1"',
        '"/public-feeds"',
        "/activate",
        "/audit",
    ):
        require(marker in router_source, f"Admin router missing {marker}")
    for forbidden in (
        "raw_storage_ref",
        "backend_object_key",
        "secret_ref",
        '"payload"',
    ):
        require(
            forbidden not in router_source,
            f"Admin router exposes forbidden field marker {forbidden}",
        )

    postgres_source = POSTGRES.read_text(encoding="utf-8")
    for marker in (
        "PostgresCanonicalPublicFeedCatalogRepository",
        "knowledge.public_feed_definition",
        "knowledge.public_feed_activation",
        "knowledge.public_feed_audit",
        "FOR UPDATE",
        "existing = self.get_definition(",
        "existing = self.get_activation_for_definition(",
        "if existing == definition:",
        "if existing == activation:",
    ):
        require(marker in postgres_source, f"PostgreSQL repository missing {marker}")

    migration_source = CANONICAL_MIGRATION.read_text(encoding="utf-8")
    for marker in (
        'revision = "20260804_0026"',
        'down_revision = "20260803_0025"',
        "guard_public_feed_definition_update",
        "guard_public_feed_activation_update",
        "reject_public_feed_audit_mutation",
    ):
        require(marker in migration_source, f"canonical migration missing {marker}")

    http_test_source = HTTP_TEST.read_text(encoding="utf-8")
    require(
        '"ADMIN_SEPARATION_OF_DUTIES" in self_approval.text' in http_test_source,
        "Admin HTTP test must assert the bounded separation-of-duties code",
    )
    require(
        '["error"]["code"]' not in http_test_source,
        "Admin HTTP test must not depend on a private error envelope",
    )

    vertical_test_source = VERTICAL_TEST.read_text(encoding="utf-8")
    require(
        "approver = _principal(AdminRole.ACCESS_ADMIN)" in vertical_test_source,
        "vertical approver must carry SOURCE_APPROVE through policy",
    )

    postgres_http_test_source = POSTGRES_HTTP_TEST.read_text(encoding="utf-8")
    require(
        'approver_id = _seed_subject(database_url, "ACCESS_ADMIN")'
        in postgres_http_test_source,
        "PostgreSQL restart approver must carry SOURCE_APPROVE through policy",
    )

    migration_names = {path.name for path in MIGRATIONS.glob("*.py")}
    require(
        not any(name.startswith("20260803_0026") for name in migration_names),
        "conflicting alternative migration 20260803_0026 entered canonical line",
    )
    print("canonical public-feed architecture PASS")


if __name__ == "__main__":
    main()
