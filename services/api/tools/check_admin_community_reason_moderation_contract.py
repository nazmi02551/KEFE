from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services" / "api"
ADR = ROOT / "docs" / "adr" / "0105-admin-community-reason-moderation-operations.md"
CONTRACT = (
    ROOT
    / "docs"
    / "contracts"
    / "admin-community-reason-moderation-operations.v1.json"
)
OVERLAY = (
    ROOT
    / "docs"
    / "contracts"
    / "openapi-admin-community-reason-moderation.v0.19.overlay.json"
)
MODELS = API / "src" / "kefe_api" / "modules" / "community_reason" / "models.py"
PORTS = API / "src" / "kefe_api" / "modules" / "community_reason" / "ports.py"
SERVICE = API / "src" / "kefe_api" / "modules" / "community_reason" / "service.py"
MEMORY = API / "src" / "kefe_api" / "modules" / "community_reason" / "in_memory.py"
POSTGRES = API / "src" / "kefe_api" / "infrastructure" / "postgres_community_reason.py"
LEGACY_ROUTER = (
    API / "src" / "kefe_api" / "modules" / "community_reason" / "admin_router.py"
)
OPERATIONS_ROUTER = (
    API
    / "src"
    / "kefe_api"
    / "modules"
    / "community_reason"
    / "moderation_operations_router.py"
)
ADMIN_MODELS = API / "src" / "kefe_api" / "modules" / "admin_security" / "models.py"
ADMIN_POLICY = API / "src" / "kefe_api" / "modules" / "admin_security" / "policy.py"
MIGRATION = (
    API
    / "migrations"
    / "versions"
    / "20260805_0027_reason_moderation_audit.py"
)
MEMORY_TEST = API / "tests" / "test_admin_community_reason_moderation_http.py"
POSTGRES_TEST = (
    API / "tests" / "test_admin_community_reason_moderation_http_postgres.py"
)
GENERATOR = (
    API / "tools" / "export_admin_community_reason_moderation_openapi_overlay.py"
)
PUBLICATION_GENERATOR = (
    API / "tools" / "export_admin_publication_operations_openapi_overlay.py"
)
WORKFLOW = ROOT / ".github" / "workflows" / "admin-community-reason-moderation.yml"
UI = ROOT / "apps" / "admin" / "src" / "components" / "reason-moderation-workspace.tsx"
UI_HELPER = ROOT / "apps" / "admin" / "src" / "lib" / "reason-moderation.ts"
UI_API = ROOT / "apps" / "admin" / "src" / "lib" / "reason-moderation-api.ts"
UI_CONTRACT = ROOT / "apps" / "admin" / "tools" / "check_reason_moderation_contract.mjs"
CROSS_SURFACE = (
    ROOT
    / "apps"
    / "mobile"
    / "docs"
    / "admin-community-reason-moderation-cross-surface-boundary.md"
)

REQUIRED = (
    ADR,
    CONTRACT,
    OVERLAY,
    MODELS,
    PORTS,
    SERVICE,
    MEMORY,
    POSTGRES,
    LEGACY_ROUTER,
    OPERATIONS_ROUTER,
    ADMIN_MODELS,
    ADMIN_POLICY,
    MIGRATION,
    MEMORY_TEST,
    POSTGRES_TEST,
    GENERATOR,
    PUBLICATION_GENERATOR,
    WORKFLOW,
    UI,
    UI_HELPER,
    UI_API,
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
        fail(f"missing reason moderation contract files: {missing_files}")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != (
        "admin-community-reason-moderation-operations.v1"
    ):
        fail("Reason moderation contract identity drifted")
    if contract.get("status") != "accepted_for_implementation":
        fail("Reason moderation contract is not accepted for implementation")
    if contract.get("parent_runtime", {}).get("sha") != (
        "9342989bf76b22036501f7792d1adb5ffb309f8b"
    ):
        fail("Reason moderation parent runtime drifted")
    if contract.get("capabilities", {}).get("primary") != ["CAP-066"]:
        fail("Reason moderation must advance CAP-066 as primary")
    if contract.get("capabilities", {}).get("lifecycle_promotion") is not False:
        fail("Reason moderation cannot silently promote capability lifecycle")

    inspection = contract.get("inspection", {})
    never_exposes = set(inspection.get("never_exposes", []))
    for field in (
        "author_actor_id",
        "weigh_session_id",
        "reporter_actor_id",
        "reporter_order",
        "inferred_user_attributes",
    ):
        if field not in never_exposes:
            fail(f"Reason moderation privacy exclusion is missing: {field}")

    decision = contract.get("decision", {})
    for key in (
        "atomic_state_and_audit",
        "actor_server_derived",
        "same_session_csrf_required",
        "recent_step_up_required",
    ):
        if decision.get(key) is not True:
            fail(f"Reason moderation decision invariant is not locked: {key}")

    models = MODELS.read_text(encoding="utf-8")
    require(
        models,
        (
            "class CommunityReasonModerationQueueKind",
            "class CommunityReasonModerationItem",
            "class CommunityReasonModerationAudit",
            "class CommunityReasonModerationWriteResult",
        ),
        "Community Reason moderation models",
    )

    ports = PORTS.read_text(encoding="utf-8")
    require(
        ports,
        (
            "def moderation_queue(",
            "def moderation_inspection(",
            "def moderation_audit(",
            "audit_id: UUID",
            "actor_ref: str",
            "rationale: str",
        ),
        "Community Reason repository contract",
    )

    service = SERVICE.read_text(encoding="utf-8")
    require(
        service,
        (
            "def moderation_queue(",
            "def moderation_inspection(",
            "def moderation_audit(",
            "COMMUNITY_REASON_MODERATION_RATIONALE_INVALID",
            "COMMUNITY_REASON_MODERATION_STATE_INVALID",
            "actor_ref=actor_ref",
        ),
        "Community Reason service",
    )

    for repository_path, label in (
        (MEMORY, "in-memory moderation repository"),
        (POSTGRES, "PostgreSQL moderation repository"),
    ):
        source = repository_path.read_text(encoding="utf-8")
        require(
            source,
            (
                "def moderation_queue(",
                "def moderation_inspection(",
                "def moderation_audit(",
                "def moderate(",
                "latest_reported_at",
                "latest_audit_at",
            ),
            label,
        )

    postgres = POSTGRES.read_text(encoding="utf-8")
    require(
        postgres,
        (
            "FOR UPDATE",
            "INSERT INTO community.reason_moderation_audit",
            "CommunityReasonModerationWriteStatus.CONFLICT",
        ),
        "PostgreSQL atomic moderation",
    )

    operations_router = OPERATIONS_ROUTER.read_text(encoding="utf-8")
    require(
        operations_router,
        (
            'prefix="/community-reason-moderation"',
            '"/{reason_id}/audit"',
            '"/{reason_id}/decision"',
            "ReadPrincipalDep",
            "WritePrincipalDep",
            "AdminCapability.CONTENT_MODERATE",
            "AdminCapability.AUDIT_READ",
            "confirm_reason_id",
            'extra="forbid"',
        ),
        "bounded reason moderation router",
    )
    for forbidden in (
        "actor_id:",
        "reporter_actor_id",
        "weigh_session_id",
        "author_actor_id",
    ):
        if forbidden in operations_router:
            fail(f"Identity field leaked into reason moderation router: {forbidden}")

    legacy_router = LEGACY_ROUTER.read_text(encoding="utf-8")
    require(
        legacy_router,
        (
            "AdminCapability.CONTENT_MODERATE",
            'request.headers.get("X-KEFE-Moderation-Rationale"',
            "actor_ref=principal.audit_actor_ref",
            "service.moderate(",
            "router.include_router(moderation_operations_router)",
        ),
        "legacy reason moderation compatibility router",
    )

    admin_models = ADMIN_MODELS.read_text(encoding="utf-8")
    admin_policy = ADMIN_POLICY.read_text(encoding="utf-8")
    require(
        admin_models,
        ('CONTENT_MODERATE = "CONTENT_MODERATE"',),
        "Admin capability model",
    )
    require(
        admin_policy,
        (
            "AdminCapability.CONTENT_MODERATE",
            "AdminRole.REVIEWER",
            "step_up_capabilities=frozenset",
        ),
        "Admin moderation policy",
    )

    migration = MIGRATION.read_text(encoding="utf-8")
    require(
        migration,
        (
            'revision = "20260805_0027"',
            'down_revision = "20260804_0026"',
            "CREATE TABLE community.reason_moderation_audit",
            "reason_moderation_audit_reason_created_idx",
        ),
        "reason moderation migration",
    )

    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")
    require(
        memory_test,
        (
            "test_moderation_queues_are_step_up_bounded_and_privacy_safe",
            "test_decision_requires_csrf_confirmation_rationale_and_appends_audit",
            "test_reported_reason_is_resolved_until_a_new_report_arrives",
            "test_blocked_reason_is_terminal_and_legacy_endpoint_cannot_bypass_audit",
        ),
        "reason moderation memory tests",
    )
    require(
        postgres_test,
        (
            "test_postgres_reason_moderation_survives_decisions_reports_and_restarts",
            "PERSONAL_DATA",
            "BLOCKED",
            "moderation_audit",
        ),
        "reason moderation PostgreSQL tests",
    )

    generator = GENERATOR.read_text(encoding="utf-8")
    publication_generator = PUBLICATION_GENERATOR.read_text(encoding="utf-8")
    require(
        generator,
        (
            "BEFORE_REASON_MODERATION_OVERLAYS",
            "openapi-admin-publication-operations.v0.19.overlay.json",
            "/internal/admin/v1/community-reason-moderation/{reason_id}/decision",
        ),
        "reason moderation OpenAPI generator",
    )
    if (
        "missing_paths" not in publication_generator
        or "new_path_names = sorted(EXPECTED_PATHS)" not in publication_generator
    ):
        fail("Predecessor Publication overlay is not isolated from later APIs")

    adr = ADR.read_text(encoding="utf-8")
    require(
        adr,
        (
            "CommunityReasonService.moderate() remains the only",
            "never expose the Community Reason author actor ID",
            "BLOCKED is terminal in this slice",
            "starts no request",
            "No automatic or bulk moderation",
        ),
        "ADR-0105",
    )

    ui = UI.read_text(encoding="utf-8")
    require(
        ui,
        (
            "ReasonModerationWorkspace",
            "loadQueue",
            "loadDetail",
            "loadAudit",
            "submitDecision",
            "Privacy-safe rapor özeti",
        ),
        "Reason moderation Admin UI",
    )
    for forbidden in (
        "useEffect(",
        "localStorage",
        "sessionStorage",
        "reporter_actor_id",
        "author_actor_id",
        "weigh_session_id",
    ):
        if forbidden in ui:
            fail(f"Forbidden behavior leaked into reason moderation UI: {forbidden}")

    workflow = WORKFLOW.read_text(encoding="utf-8")
    require(
        workflow,
        (
            "name: Admin Community Reason Moderation CI",
            "Executable backend architecture contract",
            "Exact reason moderation OpenAPI overlay",
            "Exact predecessor Publication Operations overlay",
            "Memory HTTP privacy, security and decision behavior",
            "Durable queue, report, audit and restart proof",
            "Verify Admin contracts, lint, types, tests and production build",
        ),
        "reason moderation workflow",
    )

    print(
        "Admin Community Reason moderation contract: bounded PENDING/REPORTED queues, "
        "privacy-safe report aggregates, rationale-bound atomic decisions, append-only "
        "audit, dedicated step-up capability and no alternate moderation authority verified."
    )


if __name__ == "__main__":
    main()
