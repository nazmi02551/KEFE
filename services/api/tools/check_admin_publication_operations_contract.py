from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services" / "api"
ADR = ROOT / "docs" / "adr" / "0104-admin-publication-operations-workspace.md"
CONTRACT = ROOT / "docs" / "contracts" / "admin-publication-operations-workspace.v1.json"
OVERLAY = ROOT / "docs" / "contracts" / "openapi-admin-publication-operations.v0.19.overlay.json"
ROUTER = (
    API
    / "src"
    / "kefe_api"
    / "modules"
    / "admin_security"
    / "publication_operations_router.py"
)
SECURED = API / "src" / "kefe_api" / "modules" / "admin_security" / "content_authoring.py"
SECURITY = API / "src" / "kefe_api" / "modules" / "admin_security" / "service.py"
POLICY = API / "src" / "kefe_api" / "modules" / "admin_security" / "policy.py"
SERVICE = API / "src" / "kefe_api" / "modules" / "content_authoring" / "service.py"
MODELS = API / "src" / "kefe_api" / "modules" / "content_authoring" / "models.py"
MAIN = API / "src" / "kefe_api" / "main.py"
MEMORY_TEST = API / "tests" / "test_admin_publication_operations_http.py"
POSTGRES_TEST = API / "tests" / "test_admin_publication_operations_http_postgres.py"
GENERATOR = API / "tools" / "export_admin_publication_operations_openapi_overlay.py"
FLOW_GENERATOR = API / "tools" / "export_admin_flow_composer_openapi_overlay.py"
WORKFLOW = ROOT / ".github" / "workflows" / "admin-publication-operations.yml"
UI = ROOT / "apps" / "admin" / "src" / "components" / "publication-operations-workspace.tsx"
UI_HELPER = ROOT / "apps" / "admin" / "src" / "lib" / "publication-operations.ts"
UI_CONTRACT = ROOT / "apps" / "admin" / "tools" / "check_publication_operations_contract.mjs"
CROSS_SURFACE = (
    ROOT
    / "apps"
    / "mobile"
    / "docs"
    / "admin-publication-operations-cross-surface-boundary.md"
)

REQUIRED = (
    ADR,
    CONTRACT,
    OVERLAY,
    ROUTER,
    SECURED,
    SECURITY,
    POLICY,
    SERVICE,
    MODELS,
    MAIN,
    MEMORY_TEST,
    POSTGRES_TEST,
    GENERATOR,
    FLOW_GENERATOR,
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
        fail(f"missing Publication Operations contract files: {missing_files}")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "admin-publication-operations-workspace.v1":
        fail("Publication Operations contract identity drifted")
    if contract.get("status") != "accepted_for_implementation":
        fail("Publication Operations contract is not accepted for implementation")
    if contract.get("parent_runtime", {}).get("sha") != (
        "62dd27dfa2000d818cecf16af9627c54f98a245a"
    ):
        fail("Publication Operations parent runtime drifted")
    capabilities = contract.get("capabilities", {})
    if capabilities.get("primary") != ["CAP-065"]:
        fail("Publication Operations must advance CAP-065 as primary")
    if capabilities.get("lifecycle_promotion") is not False:
        fail("Publication Operations cannot silently promote capability lifecycle")

    publish = contract.get("publish", {})
    for key in (
        "same_session_csrf_required",
        "recent_step_up_required",
        "latest_approval_audit_required",
        "publisher_must_differ_from_latest_approver",
        "canonical_validation_repeated_at_command_time",
        "canonical_resolution_repeated_at_command_time",
        "atomic_lifecycle_and_audit",
        "pins_content_configuration_and_flow",
    ):
        if publish.get(key) is not True:
            fail(f"Publication invariant is not locked: {key}")

    preflight = contract.get("preflight", {})
    for key in (
        "mutates_lifecycle",
        "writes_persistence",
        "appends_audit",
        "mutates_configuration",
        "mutates_consumer_runtime",
        "reserves_state_or_provenance",
    ):
        if preflight.get(key) is not False:
            fail(f"Preflight must be non-mutating: {key}")
    if preflight.get("final_publish_revalidates") is not True:
        fail("Final publish must revalidate after advisory preflight")

    router = ROUTER.read_text(encoding="utf-8")
    require(
        router,
        (
            'prefix="/internal/admin/v1/publication-operations"',
            '"/{version_id}/preflight"',
            '"/{version_id}/decision"',
            "PublicationQueueState",
            "acknowledge_immutable",
            "WritePrincipalDep",
            "ReadPrincipalDep",
            'extra="forbid"',
        ),
        "Publication Operations router",
    )
    for forbidden in ("save_draft(", "approve_with_review_modes(", "create_revision("):
        if forbidden in router:
            fail(f"forbidden lifecycle shortcut leaked into publication router: {forbidden}")

    secured = SECURED.read_text(encoding="utf-8")
    require(
        secured,
        (
            "def publication_queue(",
            "def publication_for_inspection(",
            "def publication_preflight(",
            "def publication_audit_context(",
            "CONTENT_PUBLICATION_APPROVAL_MISSING",
            "enforce_publisher_separation(",
            "AdminCapability.CONTENT_PUBLISH",
            "AdminCapability.CONTENT_WITHDRAW",
        ),
        "secured Content Authoring facade",
    )

    security = SECURITY.read_text(encoding="utf-8")
    require(
        security,
        (
            "def enforce_publisher_separation(",
            '"self_publish"',
            "The approving Admin cannot publish the same CaseVersion",
        ),
        "Admin security service",
    )
    policy = POLICY.read_text(encoding="utf-8")
    require(
        policy,
        (
            "publisher_must_differ_from_approver: bool = True",
            "publisher_must_differ_from_approver=True",
            "AdminCapability.CONTENT_PUBLISH",
            "AdminCapability.CONTENT_WITHDRAW",
        ),
        "Admin security policy",
    )

    service = SERVICE.read_text(encoding="utf-8")
    require(
        service,
        (
            "def publication_preflight(",
            "def _publication_preflight_for(",
            "preflight = self._publication_preflight_for(version)",
            "publish_atomically(",
            "content_configuration_id=resolution.content_configuration_id",
            "resolved_flow=resolution.resolved_flow",
        ),
        "canonical Content Authoring service",
    )
    models = MODELS.read_text(encoding="utf-8")
    require(models, ("class PublicationPreflightResult:",), "Content Authoring model")

    main_source = MAIN.read_text(encoding="utf-8")
    require(
        main_source,
        (
            "publication_operations_router",
            "app.include_router(admin_publication_operations_router)",
        ),
        "application composition",
    )

    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    require(
        memory_test,
        (
            "test_publication_queue_is_bounded_filtered_and_audit_read_only",
            "test_preflight_is_explicit_advisory_and_non_mutating",
            "test_publish_requires_csrf_step_up_ack_and_distinct_approver",
            "test_same_approver_cannot_publish_even_through_legacy_route",
            "test_withdraw_requires_rationale_and_preserves_immutable_version",
        ),
        "Publication Operations memory tests",
    )
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")
    require(
        postgres_test,
        (
            "test_postgres_publication_operations_survive_publish_withdraw_and_restart",
            "PUBLISHED",
            "WITHDRAWN",
            "Durable withdrawal proof",
        ),
        "Publication Operations PostgreSQL tests",
    )

    generator = GENERATOR.read_text(encoding="utf-8")
    require(
        generator,
        (
            "BEFORE_PUBLICATION_OVERLAYS",
            "openapi-admin-flow-composer.v0.19.overlay.json",
            "/internal/admin/v1/publication-operations/{version_id}/preflight",
            "/internal/admin/v1/publication-operations/{version_id}/decision",
        ),
        "Publication Operations OpenAPI generator",
    )
    flow_generator = FLOW_GENERATOR.read_text(encoding="utf-8")
    if (
        "missing_paths" not in flow_generator
        or "new_path_names = sorted(EXPECTED_PATHS)" not in flow_generator
    ):
        fail("Predecessor Flow Composer overlay is not isolated from later same-version APIs")

    adr = ADR.read_text(encoding="utf-8")
    require(
        adr,
        (
            "ContentAuthoringService.publish remains the only publication command",
            "Preflight is advisory",
            "publisher actor different from the latest approving reviewer actor",
            "does not delete the immutable published version",
            "starts no request on mount",
        ),
        "ADR-0104",
    )

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require(
        workflow,
        (
            "name: Admin Publication Operations CI",
            "Executable backend architecture contract",
            "Exact Publication Operations OpenAPI overlay",
            "Exact predecessor Flow Composer overlay",
            "Memory HTTP security, preflight and decision behavior",
            "Durable publish, withdraw, provenance and restart proof",
            "Verify Admin contracts, lint, types, tests and production build",
        ),
        "Publication Operations workflow",
    )

    ui = UI.read_text(encoding="utf-8")
    require(
        ui,
        (
            "Publication Operations",
            "loadQueue",
            "loadDetail",
            "runPreflight",
            "loadAudit",
            "publishConfirmed",
            "withdrawRationale",
        ),
        "Publication Operations Admin UI",
    )
    for forbidden in ("useEffect(", "localStorage", "sessionStorage", "autosave"):
        if forbidden in ui:
            fail(f"forbidden browser behavior leaked into Publication Operations UI: {forbidden}")

    print(
        "Admin Publication Operations contract: bounded queues, advisory preflight, "
        "step-up and maker-checker publish, reasoned withdraw, immutable provenance "
        "and no alternate lifecycle authority verified."
    )


if __name__ == "__main__":
    main()
