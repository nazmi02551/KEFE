from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
DOMAIN = API / "src/kefe_api/modules/knowledge/public_feed_activation_catalog.py"
POSTGRES = API / "src/kefe_api/infrastructure/postgres_public_feed_activation_catalog.py"
RUNTIME = API / "src/kefe_api/infrastructure/public_feed_activation_catalog_runtime.py"
SECURED = API / "src/kefe_api/modules/admin_security/public_feed_activation_catalog.py"
ROUTER = (
    API
    / "src/kefe_api/modules/admin_security/public_feed_activation_catalog_router.py"
)
MAIN = API / "src/kefe_api/main.py"
MIGRATION = (
    API
    / "migrations/versions/20260803_0026_public_feed_activation_catalog.py"
)
MEMORY_TEST = API / "tests/test_public_feed_activation_catalog.py"
POSTGRES_TEST = API / "tests/test_public_feed_activation_catalog_postgres.py"
ADR = (
    ROOT
    / "docs/adr/0091-immutable-public-feed-activation-catalog-and-read-only-admin-inspection.md"
)
CONTRACT = ROOT / "docs/contracts/public-feed-activation-catalog-slice55.v1.json"
WORKFLOW = ROOT / ".github/workflows/public-feed-activation-catalog-ci.yml"

REQUIRED = (
    DOMAIN,
    POSTGRES,
    RUNTIME,
    SECURED,
    ROUTER,
    MAIN,
    MIGRATION,
    MEMORY_TEST,
    POSTGRES_TEST,
    ADR,
    CONTRACT,
    WORKFLOW,
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


def method_names(node: ast.ClassDef) -> set[str]:
    return {
        item.name
        for item in node.body
        if isinstance(item, ast.FunctionDef)
    }


def fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        child.target.id
        for child in node.body
        if isinstance(child, ast.AnnAssign)
        and isinstance(child.target, ast.Name)
    )


def dataclass_keywords(node: ast.ClassDef) -> dict[str, object]:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and ast.unparse(decorator.func) == "dataclass":
            return {
                keyword.arg: keyword.value.value
                for keyword in decorator.keywords
                if keyword.arg is not None
                and isinstance(keyword.value, ast.Constant)
            }
    return {}


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing activation catalog files: {missing}")

    domain = DOMAIN.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    secured = SECURED.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")
    tests = MEMORY_TEST.read_text(encoding="utf-8") + POSTGRES_TEST.read_text(
        encoding="utf-8"
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "public-feed-activation-catalog-slice55":
        fail("activation catalog contract identity drifted")
    if contract.get("status") != "accepted":
        fail("activation catalog contract is not accepted")
    entry_contract = contract.get("entry", {})
    if entry_contract.get("manifest_schema") != (
        "kefe.public-feed-activation-manifest/1.0.0"
    ):
        fail("activation catalog manifest schema drifted")
    if entry_contract.get("manifest_encoding") != "canonical-json":
        fail("activation catalog manifest encoding drifted")
    if entry_contract.get("configuration_hash") != "sha256-canonical-json":
        fail("activation catalog hash contract drifted")
    for key in (
        "manifest_owned_on_read",
        "frozen",
        "slotted",
    ):
        if entry_contract.get(key) is not True:
            fail(f"activation catalog entry invariant drifted: {key}")
    for key in (
        "secret_ref",
        "authorization_header",
        "cookie_header",
        "backend_object_key",
    ):
        if entry_contract.get(key) is not False:
            fail(f"activation catalog sensitive field became allowed: {key}")

    classes = class_map(domain)
    entry = classes.get("PublicFeedActivationCatalogEntry")
    if entry is None or fields(entry) != (
        "id",
        "activation_code",
        "adapter_code",
        "configuration_hash",
        "manifest_schema_version",
        "manifest_json",
        "evidence_ref",
        "recorded_by",
        "recorded_at",
    ):
        fail("PublicFeedActivationCatalogEntry fields drifted")
    if dataclass_keywords(entry) != {
        "frozen": True,
        "slots": True,
        "repr": False,
    }:
        fail("catalog entry must remain frozen, slotted and repr-redacted")

    repository = classes.get("PublicFeedActivationCatalogRepository")
    if repository is None or "Protocol" not in {
        ast.unparse(base) for base in repository.bases
    }:
        fail("activation catalog repository must be a Protocol")
    expected_operations = {
        "create_or_get",
        "get_by_activation_code",
        "get_by_adapter_code",
        "list_entries",
    }
    if method_names(repository) != expected_operations:
        fail("activation catalog repository operation set drifted")

    repository_contract = contract.get("repository", {})
    if set(repository_contract.get("operations", ())) != expected_operations:
        fail("activation catalog repository contract operation set drifted")
    for operation in ("update", "delete", "enable", "schedule", "capture", "activate"):
        if repository_contract.get(operation) is not False:
            fail(f"forbidden catalog operation became enabled: {operation}")

    for fragment in (
        "canonical_manifest_json(definition.configuration_payload)",
        "canonical_manifest_hash(self.manifest_json) != self.configuration_hash",
        'payload.get("activation_code") != self.activation_code',
        'payload.get("adapter_code") != self.adapter_code',
        "return payload",
        "manifest_json=<redacted:",
        "activation manifest cannot contain a secret reference",
        "activation manifest cannot contain backend object keys",
    ):
        if fragment not in domain:
            fail(f"activation catalog domain invariant missing: {fragment}")

    for forbidden in (
        "def update",
        "def delete",
        "def enable",
        "def schedule",
        "def capture",
        "def activate",
        "requests",
        "httpx",
        "urllib.request",
        "socket",
    ):
        if forbidden in domain or forbidden in postgres:
            fail(f"forbidden catalog behavior leaked into repository: {forbidden}")
    for forbidden_sql in ("UPDATE knowledge.public_feed_activation_catalog", "DELETE FROM knowledge.public_feed_activation_catalog"):
        if forbidden_sql in postgres:
            fail(f"insert-only PostgreSQL repository contains mutation SQL: {forbidden_sql}")

    postgres_contract = contract.get("postgres", {})
    if postgres_contract != {
        "revision": "20260803_0026",
        "down_revision": "20260803_0025",
        "table": "knowledge.public_feed_activation_catalog",
        "insert_only_repository": True,
        "downgrade_blocked_when_nonempty": True,
    }:
        fail("activation catalog PostgreSQL contract drifted")
    for fragment in (
        'revision = "20260803_0026"',
        'down_revision = "20260803_0025"',
        "CREATE TABLE knowledge.public_feed_activation_catalog",
        "UNIQUE",
        "BEFORE UPDATE OR DELETE",
        "public feed activation catalog is immutable",
        "cannot downgrade while public feed activation catalog entries exist",
    ):
        if fragment not in migration:
            fail(f"activation catalog migration invariant missing: {fragment}")
    for fragment in (
        "INSERT INTO knowledge.public_feed_activation_catalog",
        "ON CONFLICT DO NOTHING",
        "resolved.catalog_content_identity == entry.catalog_content_identity",
        "ORDER BY activation_code",
    ):
        if fragment not in postgres:
            fail(f"activation catalog PostgreSQL behavior missing: {fragment}")

    if "AdminCapability.SOURCE_VERIFY" not in secured:
        fail("activation catalog Admin inspection must require SOURCE_VERIFY")
    for forbidden in (
        "create_or_get(",
        "PublicFeedActivationBundleFactory",
        "create_schedule(",
        ".capture(",
    ):
        if forbidden in secured or forbidden in router:
            fail(f"Admin inspection contains write/activation behavior: {forbidden}")

    router_tree = ast.parse(router)
    decorators = tuple(
        ast.unparse(decorator.func)
        for node in router_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for decorator in node.decorator_list
        if isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and ast.unparse(decorator.func.value) == "router"
    )
    if decorators != ("router.get", "router.get"):
        fail(f"activation catalog Admin route methods drifted: {decorators}")
    for route in (
        '"/public-feed-activations"',
        '"/public-feed-activations/{activation_code}"',
    ):
        if route not in router:
            fail(f"activation catalog Admin route missing: {route}")

    admin_contract = contract.get("admin_http", {})
    if admin_contract.get("required_capability") != "SOURCE_VERIFY":
        fail("activation catalog Admin capability contract drifted")
    if admin_contract.get("routes") != [
        "GET /internal/admin/v1/public-feed-activations",
        "GET /internal/admin/v1/public-feed-activations/{activation_code}",
    ]:
        fail("activation catalog Admin route contract drifted")
    for method_name in ("post", "put", "patch", "delete"):
        if admin_contract.get(method_name) is not False:
            fail(f"activation catalog Admin write method enabled: {method_name}")

    for fragment in (
        "build_public_feed_activation_catalog_repository(settings)",
        "app.state.public_feed_activation_catalog_repository",
        "app.state.secured_public_feed_activation_catalog_service",
        "app.include_router(admin_public_feed_activation_catalog_router)",
    ):
        if fragment not in main_source:
            fail(f"activation catalog application composition missing: {fragment}")
    for forbidden in (
        "PublicFeedActivationBundleFactory(",
        "PublicFeedActivationDefinition(",
        "build_feed_item_extraction_runtime(",
    ):
        if forbidden in main_source or forbidden in runtime:
            fail(f"production catalog composition activated a feed: {forbidden}")
    if "InMemoryPublicFeedActivationCatalogRepository()" not in runtime:
        fail("memory runtime must start with an empty activation catalog")

    production = contract.get("production", {})
    if production != {
        "catalog_entries_seeded": 0,
        "activation_bundles_built": 0,
        "schedules_installed": 0,
        "public_feed_adapters_registered": 0,
        "feed_item_workers_registered": 0,
    }:
        fail("activation catalog production boundary drifted")

    for test_name in (
        "test_catalog_entry_is_canonical_immutable_redacted_and_owned_on_read",
        "test_catalog_manifest_rejects_sensitive_fields_and_integrity_drift",
        "test_memory_catalog_is_idempotent_conflict_safe_and_deterministic",
        "test_admin_catalog_requires_authentication_and_source_verify",
        "test_admin_catalog_list_detail_pagination_and_read_only_method_matrix",
        "test_production_memory_composition_starts_with_empty_catalog",
        "test_postgres_catalog_is_idempotent_and_survives_repository_restart",
        "test_postgres_catalog_conflicts_fail_closed",
        "test_postgres_catalog_table_rejects_update_and_delete",
        "test_postgres_repository_revalidates_manifest_hash_on_read",
        "test_catalog_migration_downgrade_refuses_nonempty_table_and_preserves_head",
    ):
        if test_name not in tests:
            fail(f"activation catalog test evidence missing: {test_name}")

    for phrase in (
        "insert-only `PublicFeedActivationCatalogEntry`",
        "Canonical JSON uses sorted keys",
        "Admin inspection is authenticated and authorized with `SOURCE_VERIFY`",
        "Production builds an empty catalog repository",
        "Recording a catalog entry is not provider approval",
    ):
        if phrase not in adr:
            fail(f"ADR-0091 decision text missing: {phrase}")

    for phrase in (
        "Activation catalog architecture fitness",
        "Activation catalog memory and Admin HTTP behavior",
        "Activation catalog PostgreSQL behavior",
        "Parent public feed activation architecture fitness",
        "Parent Admin HTTP architecture fitness",
        "check_public_feed_activation_catalog_contract.py",
    ):
        if phrase not in workflow:
            fail(f"activation catalog CI step missing: {phrase}")

    print("public feed activation catalog contract: PASS")


if __name__ == "__main__":
    main()
