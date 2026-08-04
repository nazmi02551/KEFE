from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services" / "api"
ADR = ROOT / "docs" / "adr" / "0103-admin-flow-composer-draft-workspace.md"
CONTRACT = ROOT / "docs" / "contracts" / "admin-flow-composer-draft-workspace.v1.json"
OVERLAY = ROOT / "docs" / "contracts" / "openapi-admin-flow-composer.v0.19.overlay.json"
ROUTER = API / "src" / "kefe_api" / "modules" / "admin_security" / "flow_composer_router.py"
SECURED = API / "src" / "kefe_api" / "modules" / "admin_security" / "content_configuration.py"
SERVICE = API / "src" / "kefe_api" / "modules" / "content_configuration" / "service.py"
MAIN = API / "src" / "kefe_api" / "main.py"
MEMORY_TEST = API / "tests" / "test_admin_flow_composer_http.py"
POSTGRES_TEST = API / "tests" / "test_admin_flow_composer_http_postgres.py"
GENERATOR = API / "tools" / "export_admin_flow_composer_openapi_overlay.py"
WORKFLOW = ROOT / ".github" / "workflows" / "admin-flow-composer.yml"
UI = ROOT / "apps" / "admin" / "src" / "components" / "flow-composer-workspace.tsx"
UI_HELPER = ROOT / "apps" / "admin" / "src" / "lib" / "flow-composer.ts"
UI_CONTRACT = ROOT / "apps" / "admin" / "tools" / "check_flow_composer_contract.mjs"
CROSS_SURFACE = ROOT / "apps" / "mobile" / "docs" / "admin-flow-composer-cross-surface-boundary.md"

REQUIRED = (
    ADR,
    CONTRACT,
    OVERLAY,
    ROUTER,
    SECURED,
    SERVICE,
    MAIN,
    MEMORY_TEST,
    POSTGRES_TEST,
    GENERATOR,
    WORKFLOW,
    UI,
    UI_HELPER,
    UI_CONTRACT,
    CROSS_SURFACE,
)


def fail(message: str) -> None:
    raise SystemExit(message)


def require(source: str, fragments: tuple[str, ...], label: str) -> None:
    missing = [fragment for fragment in fragments if fragment not in source]
    if missing:
        fail(f"{label} missing contract fragments: {missing}")


def main() -> None:
    missing_files = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing_files:
        fail(f"missing Flow Composer contract files: {missing_files}")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "admin-flow-composer-draft-workspace.v1":
        fail("Flow Composer contract identity drifted")
    if contract.get("status") != "accepted_for_implementation":
        fail("Flow Composer contract is not accepted for implementation")
    if contract.get("parent_runtime", {}).get("sha") != (
        "f4c11547c0373017c527cfcf0a2d03dd3d3a9d97"
    ):
        fail("Flow Composer parent runtime drifted")
    capabilities = contract.get("capabilities", {})
    if capabilities.get("primary") != ["CAP-064"]:
        fail("Flow Composer must advance CAP-064 as the primary capability")
    if capabilities.get("lifecycle_promotion") is not False:
        fail("Flow Composer implementation cannot silently promote capability lifecycle")

    flow_graph = contract.get("flow_graph", {})
    for key in (
        "entry_step_required",
        "terminal_step_required",
        "all_steps_reachable_from_entry",
        "acyclic",
    ):
        if flow_graph.get(key) is not True:
            fail(f"Flow Composer graph invariant is not locked: {key}")
    if flow_graph.get("self_loop_allowed") is not False:
        fail("Flow Composer must reject self loops")

    save_semantics = contract.get("save_semantics", {})
    if save_semantics.get("only_flow_templates_replaced") is not True:
        fail("Flow Composer must replace only flow_templates")
    if save_semantics.get("non_flow_fields_preserved_server_side") is not True:
        fail("Flow Composer must preserve non-Flow fields server-side")
    if save_semantics.get("publication_side_effect") is not False:
        fail("Flow Composer save cannot publish configuration")
    if save_semantics.get("consumer_runtime_side_effect") is not False:
        fail("Flow Composer save cannot mutate consumer runtime")

    router = ROUTER.read_text(encoding="utf-8")
    require(
        router,
        (
            'prefix="/internal/admin/v1/flow-composer"',
            '"/drafts"',
            '"/configuration-versions/{version_id}"',
            '"/configuration-versions/{version_id}/audit"',
            "WritePrincipalDep",
            "ReadPrincipalDep",
            "extra=\"forbid\"",
            "configuration.save_flow_templates(",
        ),
        "Flow Composer router",
    )
    for forbidden in ('"/publish"', '"/rollback', "create_rollback_draft("):
        if forbidden in router:
            fail(f"forbidden command leaked into Flow Composer router: {forbidden}")

    secured = SECURED.read_text(encoding="utf-8")
    require(
        secured,
        (
            "def save_flow_templates(",
            "current = self.draft_for_edit(",
            "replace(current, flow_templates=flow_templates)",
            "def audit_for_version(",
            "entry.config_version_id == version_id",
        ),
        "secured content configuration facade",
    )

    service = SERVICE.read_text(encoding="utf-8")
    require(
        service,
        (
            '"CONTENT_CONFIG_FLOW_UNREACHABLE"',
            '"CONTENT_CONFIG_FLOW_CYCLIC"',
            "_reachable_step_codes(flow)",
            "_flow_has_cycle(flow)",
            "if code in visiting:",
        ),
        "content configuration graph validation",
    )

    main_source = MAIN.read_text(encoding="utf-8")
    require(
        main_source,
        (
            "flow_composer_router",
            "app.include_router(admin_flow_composer_router)",
        ),
        "application composition",
    )

    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    require(
        memory_test,
        (
            "test_flow_composer_requires_taxonomy_capability_and_same_session_csrf",
            "test_flow_composer_replaces_only_flow_templates_and_keeps_draft",
            "test_flow_composer_rejects_unreachable_and_cyclic_graphs",
            "test_flow_composer_cannot_publish_or_mutate_published_configuration",
        ),
        "Flow Composer memory tests",
    )
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")
    require(
        postgres_test,
        (
            "test_postgres_flow_composer_round_trip_survives_restart",
            "DURABLE_REVIEW_FLOW",
            "CREATE_DRAFT_FROM_CURRENT",
            "SAVE_DRAFT",
        ),
        "Flow Composer PostgreSQL tests",
    )

    generator = GENERATOR.read_text(encoding="utf-8")
    require(
        generator,
        (
            "BEFORE_FLOW_COMPOSER_OVERLAYS",
            "openapi-admin-editorial-quality-review.v0.19.overlay.json",
            "/internal/admin/v1/flow-composer/drafts",
            "/internal/admin/v1/flow-composer/configuration-versions/{version_id}",
        ),
        "Flow Composer OpenAPI generator",
    )

    adr = ADR.read_text(encoding="utf-8")
    require(
        adr,
        (
            "ContentConfigurationSnapshot remains the sole configuration and Flow authority",
            "every Step reachable from the entry Step",
            "an acyclic topology",
            "does not publish",
            "no request on mount",
        ),
        "ADR-0103",
    )

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require(
        workflow,
        (
            "name: Admin Flow Composer CI",
            "Executable backend architecture contract",
            "Exact Flow Composer OpenAPI overlay",
            "Exact predecessor Editorial Review overlay",
            "Memory HTTP behavior and graph validation",
            "Durable draft, topology and restart proof",
            "Verify Admin contracts, lint, types, tests and production build",
        ),
        "Flow Composer workflow",
    )

    ui = UI.read_text(encoding="utf-8")
    require(
        ui,
        (
            "Flow Composer",
            "DRAFT",
            "createFlowComposerDraft",
            "loadFlowComposerVersion",
            "saveFlowComposerVersion",
            "loadFlowComposerAudit",
        ),
        "Flow Composer Admin UI",
    )
    for forbidden in ("localStorage", "sessionStorage", "autosave", "dragstart"):
        if forbidden in ui:
            fail(f"forbidden browser behavior leaked into Flow Composer UI: {forbidden}")

    print(
        "Admin Flow Composer contract: DRAFT-only canonical configuration authority, "
        "safe graph validation, bounded Admin UI and no publication shortcut verified."
    )


if __name__ == "__main__":
    main()
