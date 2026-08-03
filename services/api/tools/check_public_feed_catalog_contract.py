from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
DOMAIN = API / "src/kefe_api/modules/knowledge/public_feed_catalog.py"
POSTGRES = API / "src/kefe_api/infrastructure/postgres_public_feed_catalog.py"
ROUTER = (
    API
    / "src/kefe_api/modules/admin_security/public_feed_catalog_router.py"
)
MODELS = API / "src/kefe_api/modules/admin_security/models.py"
POLICY = API / "src/kefe_api/modules/admin_security/policy.py"
SECURITY = API / "src/kefe_api/modules/admin_security/service.py"
PERSISTENCE = API / "src/kefe_api/infrastructure/persistence.py"
MAIN = API / "src/kefe_api/main.py"
MIGRATION = (
    API / "migrations/versions/20260803_0026_public_feed_catalog.py"
)
MEMORY_TEST = API / "tests/test_public_feed_catalog.py"
HTTP_TEST = API / "tests/test_public_feed_catalog_http.py"
POSTGRES_TEST = API / "tests/test_public_feed_catalog_postgres.py"
CATALOG_OPENAPI_EXPORTER = (
    API / "tools/export_public_feed_catalog_openapi_overlay.py"
)
PROPOSAL_OPENAPI_EXPORTER = (
    API / "tools/export_admin_proposal_queue_openapi_overlay.py"
)
OPENAPI_COMPOSER = API / "tools/export_openapi.py"
CATALOG_OPENAPI_OVERLAY = (
    ROOT / "docs/contracts/openapi-public-feed-catalog.v0.19.overlay.json"
)
ADR = (
    ROOT
    / "docs/adr/0091-durable-public-feed-catalog-and-secured-admin-lifecycle.md"
)
CONTRACT = ROOT / "docs/contracts/public-feed-catalog-slice55.v1.json"
WORKFLOW = ROOT / ".github/workflows/public-feed-catalog-ci.yml"

REQUIRED = (
    DOMAIN,
    POSTGRES,
    ROUTER,
    MODELS,
    POLICY,
    SECURITY,
    PERSISTENCE,
    MAIN,
    MIGRATION,
    MEMORY_TEST,
    HTTP_TEST,
    POSTGRES_TEST,
    CATALOG_OPENAPI_EXPORTER,
    PROPOSAL_OPENAPI_EXPORTER,
    OPENAPI_COMPOSER,
    CATALOG_OPENAPI_OVERLAY,
    ADR,
    CONTRACT,
    WORKFLOW,
)
CATALOG_PATHS = frozenset(
    {
        "/internal/admin/v1/public-feeds",
        "/internal/admin/v1/public-feeds/audit",
        "/internal/admin/v1/public-feeds/{entry_id}",
        "/internal/admin/v1/public-feeds/{entry_id}/approve-manual-capture",
        "/internal/admin/v1/public-feeds/{entry_id}/audit",
        "/internal/admin/v1/public-feeds/{entry_id}/retire",
    }
)


def fail(message: str) -> None:
    raise SystemExit(message)


def class_map(source: str) -> dict[str, ast.ClassDef]:
    tree = ast.parse(source)
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for child in node.body:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    fail(f"{node.name}.{name} is missing")


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing public feed catalog files: {missing}")

    domain = DOMAIN.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    models = MODELS.read_text(encoding="utf-8")
    policy = POLICY.read_text(encoding="utf-8")
    security = SECURITY.read_text(encoding="utf-8")
    persistence = PERSISTENCE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")
    catalog_exporter = CATALOG_OPENAPI_EXPORTER.read_text(encoding="utf-8")
    proposal_exporter = PROPOSAL_OPENAPI_EXPORTER.read_text(encoding="utf-8")
    openapi_composer = OPENAPI_COMPOSER.read_text(encoding="utf-8")
    catalog_overlay = json.loads(
        CATALOG_OPENAPI_OVERLAY.read_text(encoding="utf-8")
    )
    tests = "".join(
        path.read_text(encoding="utf-8")
        for path in (MEMORY_TEST, HTTP_TEST, POSTGRES_TEST)
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "public-feed-catalog-slice55":
        fail("public feed catalog contract identity drifted")
    if contract.get("status") != "accepted":
        fail("public feed catalog contract is not accepted")
    lifecycle = contract.get("lifecycle", {})
    if lifecycle.get("states") != [
        "REGISTERED",
        "MANUAL_CAPTURE_APPROVED",
        "RETIRED",
    ]:
        fail("public feed catalog lifecycle states drifted")
    if lifecycle.get("transitions") != {
        "REGISTERED": ["MANUAL_CAPTURE_APPROVED", "RETIRED"],
        "MANUAL_CAPTURE_APPROVED": ["RETIRED"],
        "RETIRED": [],
    }:
        fail("public feed catalog lifecycle transitions drifted")
    for key in (
        "definition_immutable",
        "configuration_hash_immutable",
    ):
        if lifecycle.get(key) is not True:
            fail(f"public feed catalog invariant must remain true: {key}")
    if lifecycle.get("backward_transition") is not False:
        fail("public feed catalog backward transition must remain disabled")

    classes = class_map(domain)
    for class_name in (
        "PublicFeedCatalogState",
        "PublicFeedCatalogEntry",
        "PublicFeedCatalogAuditEntry",
        "PublicFeedCatalogRepository",
        "InMemoryPublicFeedCatalogRepository",
        "PublicFeedCatalogService",
    ):
        if class_name not in classes:
            fail(f"public feed catalog class missing: {class_name}")
    entry = classes["PublicFeedCatalogEntry"]
    transition = ast.get_source_segment(domain, method(entry, "transition")) or ""
    for fragment in (
        "target not in _ALLOWED_TRANSITIONS[self.state]",
        "state=target",
        "approved_by=actor_ref",
        "retired_by=actor_ref",
        "retirement_rationale=rationale",
    ):
        if fragment not in transition:
            fail(f"catalog lifecycle guard missing: {fragment}")

    service = classes["PublicFeedCatalogService"]
    register_source = ast.get_source_segment(domain, method(service, "register")) or ""
    approve_source = ast.get_source_segment(
        domain,
        method(service, "approve_manual_capture"),
    ) or ""
    retire_source = ast.get_source_segment(domain, method(service, "retire")) or ""
    if "AdminCapability.SOURCE_MANAGE" not in register_source:
        fail("catalog registration must require SOURCE_MANAGE")
    for label, source in (("approval", approve_source), ("retirement", retire_source)):
        if "AdminCapability.SOURCE_MANAGE" not in source:
            fail(f"catalog {label} must require SOURCE_MANAGE")
        if "self._security.require_fresh_step_up(principal)" not in source:
            fail(f"catalog {label} must require fresh step-up")

    for fragment in (
        'SOURCE_MANAGE = "SOURCE_MANAGE"',
        "AdminCapability.SOURCE_MANAGE",
    ):
        if fragment not in models and fragment not in policy:
            fail(f"SOURCE_MANAGE Admin policy fragment missing: {fragment}")
    if "def require_fresh_step_up(" not in security:
        fail("Admin security service must expose fresh step-up guard")

    repository_contract = contract.get("repository", {})
    for key in (
        "memory_and_postgres_equivalent",
        "unique_feed_code",
        "unique_adapter_code",
        "idempotent_exact_registration",
        "atomic_entry_and_audit_mutation",
        "ordered_append_only_audit",
        "zero_seed_entries",
    ):
        if repository_contract.get(key) is not True:
            fail(f"public feed repository invariant must remain true: {key}")
    for fragment in (
        "FOR UPDATE",
        "existing.definition == entry.definition",
        "existing.configuration_hash == entry.configuration_hash",
        "UPDATE knowledge.public_feed_catalog",
        "self._insert_audit(connection, audit)",
        "ORDER BY audit_seq",
    ):
        if fragment not in postgres:
            fail(f"PostgreSQL catalog invariant missing: {fragment}")

    migration_contract = contract.get("migration", {})
    if migration_contract != {
        "revision": "20260803_0026",
        "down_revision": "20260803_0025",
        "schema": "knowledge",
        "clean_upgrade_downgrade_upgrade": True,
    }:
        fail("public feed catalog migration contract drifted")
    for fragment in (
        'revision = "20260803_0026"',
        'down_revision = "20260803_0025"',
        "UNIQUE",
        "public_feed_catalog_update_guard_trg",
        "public_feed lifecycle transition is invalid",
        "public_feed_catalog_audit_append_only_trg",
        "BEFORE UPDATE OR DELETE",
    ):
        if fragment not in migration:
            fail(f"public feed catalog migration invariant missing: {fragment}")

    expected_routes = (
        '@router.get("", response_model=PublicFeedCatalogListResponse)',
        '@router.get("/audit", response_model=PublicFeedCatalogAuditListResponse)',
        '@router.get("/{entry_id}", response_model=PublicFeedCatalogEntryResponse)',
        '@router.post(\n    "",',
        '"/{entry_id}/approve-manual-capture"',
        '"/{entry_id}/retire"',
    )
    for fragment in expected_routes:
        if fragment not in router:
            fail(f"public feed catalog route missing: {fragment}")
    for forbidden in (
        "SourceAcquisitionService",
        "ManualPublicFeedCaptureService",
        "build_public_feed_runtime_bundle",
        "SourceSchedulerService",
        "IngestionWorkerRunner",
        "ProviderAdoptionRegistry",
        "PublicSourceCaptureRegistry",
        "requests",
        "httpx",
        "urllib.request",
        "socket",
    ):
        if forbidden in domain or forbidden in router or forbidden in postgres:
            fail(f"forbidden runtime authority leaked into catalog: {forbidden}")

    if catalog_overlay.get("target_version") != "0.19.0":
        fail("public feed catalog OpenAPI target version drifted")
    overlay_paths = catalog_overlay.get("paths", {})
    if frozenset(overlay_paths) != CATALOG_PATHS:
        fail(f"public feed catalog OpenAPI path set drifted: {sorted(overlay_paths)}")
    overlay_schemas = catalog_overlay.get("components", {}).get("schemas", {})
    for schema_name in (
        "PublicFeedCatalogAuditListResponse",
        "PublicFeedCatalogAuditResponse",
        "PublicFeedCatalogEntryResponse",
        "PublicFeedCatalogListResponse",
        "RegisterPublicFeedRequest",
        "RetirementRequest",
        "RssAtomParseProfileInput",
        "RssAtomParseProfileResponse",
    ):
        if schema_name not in overlay_schemas:
            fail(f"public feed catalog OpenAPI schema missing: {schema_name}")
    if "HTTPValidationError" in overlay_schemas:
        fail("catalog OpenAPI overlay must not duplicate base schemas")
    for fragment in (
        'CATALOG_PATH_PREFIX = "/internal/admin/v1/public-feeds"',
        "_schema_reference_closure(",
        '"target_version": "0.19.0"',
    ):
        if fragment not in catalog_exporter:
            fail(f"catalog OpenAPI exporter invariant missing: {fragment}")
    if 'PROPOSAL_PATH_PREFIX = "/internal/admin/v1/proposals"' not in proposal_exporter:
        fail("Proposal Queue OpenAPI exporter is not path-scoped")
    catalog_overlay_position = openapi_composer.find(
        '"openapi-public-feed-catalog.v0.19.overlay.json"'
    )
    proposal_overlay_position = openapi_composer.find(
        '"openapi-admin-proposal-queue.v0.19.overlay.json"'
    )
    if not 0 <= proposal_overlay_position < catalog_overlay_position:
        fail("catalog OpenAPI overlay must compose after Proposal Queue overlay")

    composition = contract.get("composition", {})
    for key in (
        "repository_composed",
        "secured_service_composed",
        "router_composed",
    ):
        if composition.get(key) is not True:
            fail(f"catalog composition must remain enabled: {key}")
    for key in (
        "runtime_bundle_constructed",
        "capture_adapter_registered",
        "provider_admission_mutated",
        "scheduler_mutated",
        "automatic_review",
        "automatic_materialization",
        "automatic_publication",
    ):
        if composition.get(key) is not False:
            fail(f"catalog composition must remain disabled: {key}")
    if composition.get("network_calls") != 0:
        fail("catalog composition cannot make network calls")
    if composition.get("ingestion_worker_runs") != 0:
        fail("catalog composition cannot run ingestion workers")
    for fragment in (
        "build_public_feed_catalog_repository(settings)",
        "PublicFeedCatalogService(",
        "app.state.public_feed_catalog_service",
        "app.include_router(admin_public_feed_catalog_router)",
    ):
        if fragment not in persistence and fragment not in main_source:
            fail(f"public feed catalog startup composition missing: {fragment}")
    if "build_public_feed_runtime_bundle(" in main_source:
        fail("production startup cannot construct public feed runtime bundle")

    for test_name in (
        "test_catalog_entry_is_immutable_and_lifecycle_is_one_way",
        "test_registration_is_exactly_idempotent_without_duplicate_audit",
        "test_source_manage_authorization_and_step_up_boundaries",
        "test_approval_retirement_and_ordered_audit_are_atomic",
        "test_catalog_mutations_require_same_session_csrf",
        "test_register_list_detail_audit_and_strict_payload",
        "test_approval_and_retirement_require_fresh_step_up",
        "test_postgres_registration_replay_restart_and_conflicts",
        "test_postgres_lifecycle_and_ordered_audit_survive_restart",
        "test_postgres_definition_lifecycle_and_audit_triggers_fail_closed",
    ):
        if test_name not in tests:
            fail(f"public feed catalog test evidence missing: {test_name}")

    for phrase in (
        "REGISTERED → MANUAL_CAPTURE_APPROVED → RETIRED",
        "SOURCE_MANAGE",
        "fresh step-up authentication",
        "Zero catalog entries are seeded",
    ):
        if phrase not in adr:
            fail(f"ADR-0091 decision text missing: {phrase}")

    for phrase in (
        "Public feed catalog architecture fitness",
        "Public feed catalog OpenAPI overlay exact gate",
        "Composed OpenAPI exact gate",
        "Public feed catalog memory and Admin HTTP behavior",
        "Public feed catalog PostgreSQL behavior",
        "check_public_feed_catalog_contract.py",
    ):
        if phrase not in workflow:
            fail(f"public feed catalog CI step missing: {phrase}")

    print("public feed catalog contract: PASS")


if __name__ == "__main__":
    main()
