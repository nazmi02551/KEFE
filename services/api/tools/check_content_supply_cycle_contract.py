from __future__ import annotations

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs" / "contracts" / "content-supply-process-cycle-slice41.v1.json"
MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260802_0023_content_supply_cycle.py"
)
MODULE = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "content_supply_cycle"
MODELS = MODULE / "models.py"
PORTS = MODULE / "ports.py"
MEMORY = MODULE / "in_memory.py"
SERVICE = MODULE / "service.py"
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_content_supply_cycle.py"
)
CLI = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "run_content_supply_cycle.py"
)
PIPELINE = (
    REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "infrastructure" / "editorial_pipeline.py"
)
MAIN = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "main.py"
MEMORY_TEST = REPO_ROOT / "services" / "api" / "tests" / "test_content_supply_cycle.py"
CLI_TEST = REPO_ROOT / "services" / "api" / "tests" / "test_content_supply_cycle_cli.py"
POSTGRES_TEST = REPO_ROOT / "services" / "api" / "tests" / "test_content_supply_cycle_postgres.py"


def _require(
    problems: list[str],
    label: str,
    content: str,
    fragments: tuple[str, ...],
) -> None:
    for fragment in fragments:
        if fragment not in content:
            problems.append(f"{label} missing: {fragment}")


def _dataclass_fields(source: str, class_name: str) -> tuple[str, ...]:
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return tuple(
                statement.target.id
                for statement in node.body
                if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name)
            )
    return ()


def main() -> int:
    required = (
        CONTRACT,
        MIGRATION,
        MODELS,
        PORTS,
        MEMORY,
        SERVICE,
        POSTGRES,
        CLI,
        PIPELINE,
        MAIN,
        MEMORY_TEST,
        CLI_TEST,
        POSTGRES_TEST,
    )
    missing = [path for path in required if not path.exists()]
    if missing:
        for path in missing:
            print(f"missing required file: {path.relative_to(REPO_ROOT)}")
        return 1

    problems: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    migration = MIGRATION.read_text(encoding="utf-8")
    models = MODELS.read_text(encoding="utf-8")
    ports = PORTS.read_text(encoding="utf-8")
    memory = MEMORY.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    cli = CLI.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    cli_test = CLI_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")

    command = contract.get("command", {})
    if command.get("immutable") is not True:
        problems.append("cycle command must remain immutable")
    if command.get("exact_pipeline_targets") is not True:
        problems.append("cycle pipeline targets must remain exact")
    if command.get("duplicate_pipeline_targets_rejected") is not True:
        problems.append("duplicate pipeline target rejection is not locked")
    bounded = contract.get("bounded_execution", {})
    if bounded.get("one_shot") is not True:
        problems.append("process cycle must remain one-shot")
    if bounded.get("continuous_loop") is not False:
        problems.append("continuous cycle loop must remain excluded")
    if bounded.get("sleep_or_polling") is not False:
        problems.append("sleep/polling must remain excluded")
    journal = contract.get("journal", {})
    if journal.get("stale_recovery_target") != "ABANDONED":
        problems.append("stale cycles must recover only to ABANDONED")
    if journal.get("stale_recovery_mutates_delegated_work") is not False:
        problems.append("cycle recovery may not mutate delegated work")
    if contract.get("cli", {}).get("daemon_mode") is not False:
        problems.append("CLI daemon mode must remain excluded")

    result_fields = _dataclass_fields(service, "ContentSupplyCycleResult")
    expected_result_fields = tuple(contract.get("observer", {}).get("allowed_fields", ()))
    if result_fields != expected_result_fields:
        problems.append("ContentSupplyCycleResult allowlist drifted: " + ", ".join(result_fields))

    _require(
        problems,
        "cycle migration",
        migration,
        (
            'revision = "20260802_0023"',
            'down_revision = "20260802_0022"',
            "CREATE TABLE ingestion.content_supply_cycle",
            "'RUNNING','IDLE','SUCCEEDED'",
            "'DEGRADED','FAILED','ABANDONED'",
            "content_supply_cycle_running_expiry_idx",
            "content_supply_cycle_completed_idx",
            "DROP TABLE IF EXISTS ingestion.content_supply_cycle",
        ),
    )
    _require(
        problems,
        "cycle models",
        models,
        (
            "class ContentSupplyPipelineTarget:",
            "class ContentSupplyCycleCommand:",
            "duplicate content-supply pipeline target",
            "def plan_hash(self) -> str:",
            "class ContentSupplyCycleState(StrEnum):",
            'ABANDONED = "ABANDONED"',
            "class ContentSupplyCycleCounters:",
            "def require_active_owner(",
            "def heartbeat(",
            "cycle counters must be monotonic",
            "def abandon(",
            'error_code="CONTENT_SUPPLY_CYCLE_STALE"',
        ),
    )
    _require(
        problems,
        "cycle repository port",
        ports,
        (
            "class ContentSupplyCycleRepository(Protocol):",
            "def create(",
            "def heartbeat(",
            "def complete(",
            "def recover_stale(",
        ),
    )
    _require(
        problems,
        "memory journal",
        memory,
        (
            "with self._lock:",
            "cycle.heartbeat(",
            "cycle.complete(",
            "cycle.abandon(at=at)",
        ),
    )
    _require(
        problems,
        "PostgreSQL journal",
        postgres,
        (
            "SELECT *",
            "FOR UPDATE",
            "FOR UPDATE SKIP LOCKED",
            "cycle.heartbeat(",
            "cycle.complete(",
            ".abandon(at=at)",
        ),
    )
    if " OFFSET " in postgres.upper():
        problems.append("cycle stale recovery may not use OFFSET")
    _require(
        problems,
        "bounded cycle service",
        service,
        (
            "class ContentSupplyCycleService:",
            "def run_once(",
            "for _ in range(command.plan_budget):",
            "for dispatch_index in range(command.dispatch_budget):",
            "for run_index in range(target.max_runs):",
            "if planned is None:",
            "SourceDispatchExecutionOutcome.IDLE",
            "IngestionWorkerRunOutcome.IDLE",
            "ContentSupplyCycleState.DEGRADED",
            "CONTENT_SUPPLY_DELEGATED_NON_SUCCESS",
            "CONTENT_SUPPLY_CYCLE_UNEXPECTED_FAILURE",
            "ContentSupplyCycleOutcome.LEASE_LOST",
        ),
    )
    plan_position = service.find("for _ in range(command.plan_budget):")
    dispatch_position = service.find("for dispatch_index in range(command.dispatch_budget):")
    ingestion_position = service.find("for target in command.pipeline_targets:")
    if not 0 <= plan_position < dispatch_position < ingestion_position:
        problems.append("content-supply phase order drifted")

    _require(
        problems,
        "cycle CLI",
        cli,
        (
            "def parse_pipeline_target(",
            "CODE@VERSION:MAX_RUNS",
            "def exit_code_for(",
            "return 2",
            "return 3",
            "INVALID_INPUT_EXIT_CODE = 64",
            "json.dumps(result.as_operational_dict(), sort_keys=True)",
            "content_supply_cycle_service.run_once(command)",
        ),
    )
    _require(
        problems,
        "composition",
        pipeline,
        (
            "InMemoryContentSupplyCycleRepository()",
            "PostgresContentSupplyCycleRepository(engine)",
            "NoOpContentSupplyCycleObserver()",
            "ContentSupplyCycleService(",
            "content_supply_cycle_service=content_supply_cycle_service",
        ),
    )
    _require(
        problems,
        "application state",
        main_source,
        (
            "app.state.content_supply_cycle_repository",
            "app.state.content_supply_cycle_observer",
            "app.state.content_supply_cycle_service",
        ),
    )
    _require(
        problems,
        "memory evidence",
        memory_test,
        (
            "test_cycle_command_plan_hash_is_deterministic_and_targets_are_exact",
            "test_bounded_phase_order_stops_each_phase_on_idle",
            "test_phase_budgets_bound_non_idle_work",
            "test_delegated_non_success_completes_degraded_without_retry_policy",
            "test_unexpected_supervisor_failure_is_bounded_and_privacy_safe",
            "test_cycle_lease_loss_fails_closed_and_stale_cycle_is_abandoned",
            "test_observer_failure_is_non_authoritative_and_result_allowlist_is_exact",
        ),
    )
    _require(
        problems,
        "CLI evidence",
        cli_test,
        (
            "test_cli_invokes_exact_one_shot_command_and_prints_allowlist_json",
            "test_cli_exit_codes_are_deterministic",
            "test_cli_invalid_input_returns_usage_exit_without_running_service",
        ),
    )
    _require(
        problems,
        "PostgreSQL evidence",
        postgres_test,
        (
            "test_postgres_cycle_heartbeat_and_completion_require_exact_owner",
            "test_postgres_stale_cycle_recovery_marks_abandoned_only",
            "test_postgres_concurrent_stale_recovery_abandons_cycle_once",
            "test_postgres_terminal_cycle_is_not_changed_by_stale_recovery",
            "ThreadPoolExecutor",
            "Barrier(2)",
        ),
    )

    combined_domain = models + ports + memory + service
    forbidden_fragments = (
        "while True",
        "time.sleep",
        "from time import sleep",
        "croniter",
        "crontab",
        "APIRouter",
        "import requests",
        "import httpx",
        "from openai",
        "import openai",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "publish(",
    )
    for fragment in forbidden_fragments:
        if fragment in combined_domain or fragment in cli:
            problems.append(f"excluded behavior leaked into cycle runtime: {fragment}")

    forbidden_fields = set(contract.get("observer", {}).get("forbidden_fields", ()))
    if forbidden_fields.intersection(result_fields):
        problems.append("forbidden sensitive field entered cycle result")

    if problems:
        print("Content supply process cycle contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Content supply process cycle contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
