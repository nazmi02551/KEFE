from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
DOMAIN = API / "src/kefe_api/modules/knowledge/public_feed_manual_capture.py"
RUNTIME = (
    API / "src/kefe_api/infrastructure/public_feed_manual_capture_runtime.py"
)
PERSISTENCE = (
    API / "src/kefe_api/infrastructure/public_feed_manual_capture_persistence.py"
)
POSTGRES = (
    API / "src/kefe_api/infrastructure/postgres_public_feed_manual_capture.py"
)
ROUTER = (
    API
    / "src/kefe_api/modules/admin_security/public_feed_manual_capture_router.py"
)
MAIN = API / "src/kefe_api/main.py"
MIGRATION = (
    API
    / "migrations/versions/20260803_0027_public_feed_manual_capture_audit.py"
)
BEHAVIOR_TEST = API / "tests/test_public_feed_manual_capture.py"
HTTP_TEST = API / "tests/test_public_feed_manual_capture_http.py"
POSTGRES_TEST = API / "tests/test_public_feed_manual_capture_postgres.py"
ADR = (
    ROOT
    / "docs/adr/0092-approved-public-feed-manual-capture-execution.md"
)
CONTRACT = ROOT / "docs/contracts/public-feed-manual-capture-slice56.v1.json"
WORKFLOW = ROOT / ".github/workflows/public-feed-manual-capture-ci.yml"

REQUIRED = (
    DOMAIN,
    RUNTIME,
    PERSISTENCE,
    POSTGRES,
    ROUTER,
    MAIN,
    MIGRATION,
    BEHAVIOR_TEST,
    HTTP_TEST,
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


def method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for child in node.body:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    fail(f"{node.name}.{name} is missing")


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing public feed manual capture files: {missing}")

    domain = DOMAIN.read_text(encoding="utf-8")
    runtime = RUNTIME.read_text(encoding="utf-8")
    persistence = PERSISTENCE.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    router = ROUTER.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    migration = MIGRATION.read_text(encoding="utf-8")
    tests = "".join(
        path.read_text(encoding="utf-8")
        for path in (BEHAVIOR_TEST, HTTP_TEST, POSTGRES_TEST)
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "public-feed-manual-capture-slice56":
        fail("manual public feed capture contract identity drifted")
    if contract.get("status") != "accepted":
        fail("manual public feed capture contract is not accepted")

    authorization = contract.get("authorization", {})
    if authorization != {
        "capability": "SOURCE_MANAGE",
        "csrf_required": True,
        "fresh_step_up_required": True,
        "server_derived_actor": True,
    }:
        fail("manual public feed capture authorization contract drifted")
    catalog_gate = contract.get("catalog_gate", {})
    if catalog_gate != {
        "required_state": "MANUAL_CAPTURE_APPROVED",
        "registered_allowed": False,
        "retired_allowed": False,
        "request_may_supply_runtime_fields": False,
        "immutable_definition_source": True,
        "configuration_hash_verified": True,
    }:
        fail("manual public feed capture catalog gate drifted")

    classes = class_map(domain)
    for class_name in (
        "PublicFeedManualCaptureAuditEntry",
        "PublicFeedManualCaptureAuditRepository",
        "InMemoryPublicFeedManualCaptureAuditRepository",
        "PublicFeedManualCaptureRuntime",
        "PublicFeedManualCaptureExecutionResult",
        "ApprovedPublicFeedManualCaptureService",
    ):
        if class_name not in classes:
            fail(f"manual public feed capture class missing: {class_name}")
    service = classes["ApprovedPublicFeedManualCaptureService"]
    capture = ast.get_source_segment(domain, method(service, "capture_once")) or ""
    for fragment in (
        "AdminCapability.SOURCE_MANAGE",
        "self._security.require_fresh_step_up(principal, now=now)",
        "entry.state is not PublicFeedCatalogState.MANUAL_CAPTURE_APPROVED",
        "entry.configuration_hash != entry.definition.configuration_hash",
        "actor_ref=principal.audit_actor_ref",
        'outcome="ATTEMPT_STARTED"',
        "self._runtime.execute(",
        "outcome=acquisition.outcome.value",
    ):
        if fragment not in capture:
            fail(f"manual capture service guard missing: {fragment}")
    started_position = capture.find('outcome="ATTEMPT_STARTED"')
    started_append_position = capture.find("self._audit.append(started)")
    execute_position = capture.find("self._runtime.execute(")
    terminal_position = capture.find("terminal = PublicFeedManualCaptureAuditEntry(")
    terminal_append_position = capture.find("self._audit.append(terminal)")
    if not (
        0
        <= started_position
        < started_append_position
        < execute_position
        < terminal_position
        < terminal_append_position
    ):
        fail("manual capture audit/execute order drifted")
    if capture.count("self._runtime.execute(") != 1:
        fail("manual capture service must execute runtime exactly once")

    runtime_contract = contract.get("runtime", {})
    if runtime_contract.get("scope") != "INVOCATION":
        fail("manual capture runtime must remain invocation scoped")
    if runtime_contract.get("global_registry_mutation") is not False:
        fail("manual capture cannot mutate global registries")
    if runtime_contract.get("source_acquisition_commands_per_invocation") != 1:
        fail("manual capture must emit one command")
    if runtime_contract.get("source_acquisition_attempts_per_invocation") != 1:
        fail("manual capture must emit one attempt")
    for fragment in (
        "InMemoryProviderAdoptionRegistry((profile,))",
        "ControlledProviderHttpTransport(",
        "EvidenceBackedPublicHttpCaptureAdapterFactory(",
        "StrictRssAtomCaptureDefinition(",
        "InMemoryPublicSourceCaptureRegistry((adapter,))",
        "PermitBoundPublicCaptureExecutor(",
        "SourceAcquisitionService(",
        "return acquisition.acquire(",
        "credential_mode=ProviderCredentialMode.PUBLIC",
    ):
        if fragment not in runtime:
            fail(f"invocation runtime invariant missing: {fragment}")
    if runtime.count("return acquisition.acquire(") != 1:
        fail("invocation runtime must acquire exactly once")
    for forbidden in (
        "SourceSchedulerService",
        "create_schedule(",
        "execute_pending_once(",
        "IngestionWorkerRunner",
        "run_once(",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "create_case",
        "publish(",
    ):
        if forbidden in domain or forbidden in runtime or forbidden in router:
            fail(f"forbidden downstream authority leaked into manual capture: {forbidden}")

    audit_contract = contract.get("audit", {})
    if audit_contract.get("append_only") is not True:
        fail("manual capture audit must remain append-only")
    for key in (
        "locator_stored",
        "raw_body_stored",
        "credential_or_secret_stored",
        "headers_stored",
        "exception_text_stored",
    ):
        if audit_contract.get(key) is not False:
            fail(f"manual capture audit forbidden field drifted: {key}")
    for forbidden in (
        "external_locator",
        "raw_storage_ref",
        "secret_ref",
        "headers",
        "exception_text",
    ):
        if forbidden in postgres:
            fail(f"manual capture PostgreSQL audit stores forbidden field: {forbidden}")
    for fragment in (
        "ORDER BY audit_seq",
        "INSERT INTO knowledge.public_feed_manual_capture_audit",
    ):
        if fragment not in postgres:
            fail(f"manual capture PostgreSQL audit invariant missing: {fragment}")

    migration_contract = contract.get("migration", {})
    if migration_contract != {
        "revision": "20260803_0027",
        "down_revision": "20260803_0026",
        "schema": "knowledge",
        "clean_upgrade_downgrade_upgrade": True,
    }:
        fail("manual capture migration contract drifted")
    for fragment in (
        'revision = "20260803_0027"',
        'down_revision = "20260803_0026"',
        "public_feed_manual_capture_audit_append_only_trg",
        "BEFORE UPDATE OR DELETE",
        "ATTEMPT_STARTED",
    ):
        if fragment not in migration:
            fail(f"manual capture migration invariant missing: {fragment}")

    http_contract = contract.get("http", {})
    if http_contract.get("request_body") is not False:
        fail("manual capture HTTP request body must remain disabled")
    for fragment in (
        '"/{entry_id}/capture-once"',
        '"/capture-audit"',
        '"/{entry_id}/capture-audit"',
        "WritePrincipalDep",
        "ReadPrincipalDep",
        'Header(alias="X-KEFE-Trace-ID"',
    ):
        if fragment not in router:
            fail(f"manual capture HTTP invariant missing: {fragment}")
    for forbidden in (
        "RegisterPublicFeedRequest",
        "external_locator:",
        "adapter_code:",
        "parser_profile:",
        "quota_limit:",
    ):
        capture_route = router.split("def capture_public_feed_once", 1)[1]
        if forbidden in capture_route.split("def _result_response", 1)[0]:
            fail(f"runtime field leaked into manual capture request: {forbidden}")

    composition = contract.get("composition", {})
    if composition.get("service_composed") is not True:
        fail("manual capture service must be composed")
    if composition.get("runtime_factory_composed") is not True:
        fail("manual capture runtime factory must be composed")
    if composition.get("catalog_entries_seeded") != 0:
        fail("manual capture composition must seed zero entries")
    if composition.get("global_adoption_profiles_registered") != 0:
        fail("manual capture cannot register global adoption profiles")
    if composition.get("global_public_adapters_registered") != 0:
        fail("manual capture cannot register global public adapters")
    for fragment in (
        "build_public_feed_manual_capture_audit_repository(settings)",
        "InvocationScopedPublicFeedManualCaptureRuntime(",
        "ApprovedPublicFeedManualCaptureService(",
        "app.state.public_feed_manual_capture_service",
        "app.include_router(admin_public_feed_manual_capture_router)",
    ):
        if fragment not in persistence and fragment not in main_source:
            fail(f"manual capture startup composition missing: {fragment}")

    for test_name in (
        "test_registered_retired_and_missing_entries_never_execute",
        "test_fresh_step_up_and_started_audit_are_required_before_runtime",
        "test_one_invocation_emits_one_runtime_attempt_and_two_audit_events",
        "test_runtime_exception_is_bounded_and_terminally_audited",
        "test_full_approved_capture_commits_source_and_only_queues_ingestion",
        "test_manual_capture_requires_session_csrf_capability_and_step_up",
        "test_approved_capture_uses_header_trace_and_returns_bounded_result",
        "test_invalid_trace_is_rejected_before_runtime_or_audit",
        "test_postgres_manual_capture_audit_survives_restart",
        "test_postgres_manual_capture_audit_is_append_only",
    ):
        if test_name not in tests:
            fail(f"manual capture test evidence missing: {test_name}")

    for phrase in (
        "ephemeral exact runtime",
        "Exactly one `SourceAcquisitionCommand`",
        "never runs an ingestion worker",
        "never stores the locator",
        "seeds zero catalog entries",
    ):
        if phrase not in adr:
            fail(f"ADR-0092 decision text missing: {phrase}")

    for phrase in (
        "Manual public feed capture architecture fitness",
        "Manual public feed capture memory and HTTP behavior",
        "Manual public feed capture PostgreSQL behavior",
        "check_public_feed_manual_capture_contract.py",
    ):
        if phrase not in workflow:
            fail(f"manual capture CI step missing: {phrase}")

    print("public feed manual capture contract: PASS")


if __name__ == "__main__":
    main()
