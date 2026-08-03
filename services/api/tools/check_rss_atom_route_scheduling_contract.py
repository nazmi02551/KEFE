from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
SCHEDULING = (
    API
    / "src/kefe_api/modules/knowledge/rss_atom_route_scheduling.py"
)
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
MEMORY_TEST = API / "tests/test_rss_atom_route_scheduling.py"
POSTGRES_TEST = API / "tests/test_rss_atom_route_scheduling_postgres.py"
ADR = (
    ROOT
    / "docs/adr/0091-route-bound-rss-atom-schedule-creation-and-deterministic-reconciliation.md"
)
CONTRACT = ROOT / "docs/contracts/rss-atom-route-scheduling-slice55.v1.json"
WORKFLOW = ROOT / ".github/workflows/rss-atom-route-scheduling-ci.yml"

REQUIRED = (
    SCHEDULING,
    PIPELINE,
    MEMORY_TEST,
    POSTGRES_TEST,
    ADR,
    CONTRACT,
    WORKFLOW,
)


def fail(message: str) -> None:
    raise SystemExit(message)


def class_map(source: str) -> dict[str, ast.ClassDef]:
    return {
        node.name: node
        for node in ast.parse(source).body
        if isinstance(node, ast.ClassDef)
    }


def fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        child.target.id
        for child in node.body
        if isinstance(child, ast.AnnAssign)
        and isinstance(child.target, ast.Name)
    )


def method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for child in node.body:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    fail(f"{node.name}.{name} is missing")


def segment(source: str, node: ast.AST) -> str:
    return ast.get_source_segment(source, node) or ""


def arguments(node: ast.FunctionDef) -> tuple[str, ...]:
    return tuple(
        argument.arg
        for argument in (*node.args.args, *node.args.kwonlyargs)
    )


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing RSS/Atom route scheduling files: {missing}")

    scheduling = SCHEDULING.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    tests = MEMORY_TEST.read_text(encoding="utf-8") + POSTGRES_TEST.read_text(
        encoding="utf-8"
    )
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "rss-atom-route-scheduling-slice55":
        fail("route scheduling contract identity drifted")
    if contract.get("status") != "accepted":
        fail("route scheduling contract is not accepted")
    request_contract = contract.get("request", {})
    if request_contract.get("fields") != [
        "route_code",
        "external_locator",
        "first_due_at",
        "interval_seconds",
        "max_dispatch_attempts",
    ]:
        fail("route schedule request contract drifted")
    for name in (
        "adapter_override",
        "pipeline_override",
        "configuration_override",
        "locale_override",
        "jurisdiction_override",
    ):
        if request_contract.get(name) is not False:
            fail(f"route schedule override must remain disabled: {name}")

    delegation = contract.get("delegation", {})
    if delegation.get("generic_scheduler_create") is not True:
        fail("route scheduling must delegate creation")
    for name in (
        "new_schedule_state_machine",
        "new_lease_state_machine",
        "new_retry_loop",
        "new_dispatch_executor",
    ):
        if delegation.get(name) is not False:
            fail(f"route scheduling duplicated generic authority: {name}")

    classes = class_map(scheduling)
    for class_name in (
        "RssAtomRouteScheduleError",
        "RssAtomRouteScheduleRequest",
        "RssAtomRouteScheduleService",
    ):
        if class_name not in classes:
            fail(f"route scheduling class is missing: {class_name}")

    request = classes["RssAtomRouteScheduleRequest"]
    if fields(request) != (
        "route_code",
        "external_locator",
        "first_due_at",
        "interval_seconds",
        "max_dispatch_attempts",
    ):
        fail("RssAtomRouteScheduleRequest fields drifted")

    service = classes["RssAtomRouteScheduleService"]
    create = method(service, "create")
    if arguments(create) != ("self", "request", "now"):
        fail("route schedule create exposes override authority")
    create_source = segment(scheduling, create)
    ordered = (
        "self._get_route(request.route_code)",
        "route.acquisition_command(request.external_locator)",
        "self._scheduler.create_schedule(",
        "build_source_schedule_key(",
        "self._require_schedule_matches(",
    )
    positions = tuple(create_source.find(fragment) for fragment in ordered)
    if any(position < 0 for position in positions) or positions != tuple(
        sorted(positions)
    ):
        fail("route schedule derivation/delegation order drifted")
    for fragment in (
        "adapter_code=command.adapter_code",
        "pipeline_code=command.pipeline_code",
        "pipeline_version=command.pipeline_version",
        "configuration_hash=command.configuration_hash",
        "locale=command.locale",
        "jurisdiction_code=command.jurisdiction_code",
        "schedule.schedule_key != expected_key",
    ):
        if fragment not in create_source:
            fail(f"route-derived schedule field missing: {fragment}")

    reconcile = method(service, "reconcile")
    reconcile_source = segment(scheduling, reconcile)
    if "self._routes.get_by_adapter_code(schedule.adapter_code)" not in (
        reconcile_source
    ):
        fail("route reconciliation must resolve by unique adapter code")
    match_source = segment(scheduling, method(service, "_require_schedule_matches"))
    for field_name in (
        "adapter_code",
        "pipeline_code",
        "pipeline_version",
        "configuration_hash",
        "taxonomy_version",
        "methodology_version",
        "locale",
        "jurisdiction_code",
    ):
        if f"command.{field_name}" not in match_source or (
            f"schedule.{field_name}" not in match_source
        ):
            fail(f"route schedule reconciliation field missing: {field_name}")

    for forbidden in (
        "SourceAcquisitionDispatch(",
        "claim_pending_once(",
        "heartbeat(",
        "recover_stale(",
        "execute_pending_once(",
        "while True",
        "time.sleep",
        "SecretAccess",
        "use_bytes",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "publish(",
        "create_case",
        "requests",
        "httpx",
        "socket",
    ):
        if forbidden in scheduling:
            fail(f"forbidden authority leaked into route scheduling: {forbidden}")

    for phrase in (
        "RssAtomRouteScheduleService(",
        "rss_atom_route_schedule_service",
    ):
        if phrase not in pipeline:
            fail(f"production route scheduling composition missing: {phrase}")
    if "RssAtomRouteScheduleRequest(" in pipeline:
        fail("production composition must create zero route schedules")
    composition = contract.get("composition", {})
    if composition.get("production_route_registry_entries") != 0:
        fail("production route registry must remain empty")
    if composition.get("production_route_schedules_created") != 0:
        fail("production route schedules must remain zero")

    for test_name in (
        "test_route_schedule_derives_exact_command_key_and_is_idempotent",
        "test_route_schedule_missing_route_and_command_drift_fail_closed",
        "test_generic_scheduler_retains_route_schedule_lifecycle_authority",
        "test_scheduled_route_dispatch_reaches_review_required_feed_item_proposals",
        "test_postgres_route_schedule_create_is_idempotent_and_reconcilable",
    ):
        if test_name not in tests:
            fail(f"route scheduling test evidence missing: {test_name}")

    for phrase in (
        "Callers supply only route code",
        "does not duplicate schedule persistence",
        "Any drift fails closed",
        "No schema column is added solely for route code",
        "production route registry remains empty",
    ):
        if phrase not in adr:
            fail(f"ADR-0091 decision text missing: {phrase}")

    for phrase in (
        "RSS Atom route scheduling architecture fitness",
        "RSS Atom route scheduling behavior",
        "RSS Atom route scheduling PostgreSQL",
        "Parent source scheduler architecture fitness",
        "Parent RSS Atom route architecture fitness",
        "check_rss_atom_route_scheduling_contract.py",
    ):
        if phrase not in workflow:
            fail(f"route scheduling CI step missing: {phrase}")

    print("RSS Atom route scheduling contract: PASS")


if __name__ == "__main__":
    main()
