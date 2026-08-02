from __future__ import annotations

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "source-acquisition-scheduler-slice40.v1.json"
)
MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260802_0022_source_acquisition_scheduler.py"
)
KNOWLEDGE = (
    REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "knowledge"
)
DOMAIN = KNOWLEDGE / "source_scheduler.py"
PORT = KNOWLEDGE / "source_scheduler_ports.py"
MEMORY = KNOWLEDGE / "source_scheduler_memory.py"
SERVICE = KNOWLEDGE / "source_scheduler_service.py"
ACQUISITION = KNOWLEDGE / "source_acquisition.py"
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_source_acquisition_scheduler.py"
)
PIPELINE = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "editorial_pipeline.py"
)
MAIN = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "main.py"
MEMORY_TEST = (
    REPO_ROOT / "services" / "api" / "tests" / "test_source_acquisition_scheduler.py"
)
POSTGRES_TEST = (
    REPO_ROOT
    / "services"
    / "api"
    / "tests"
    / "test_source_acquisition_scheduler_postgres.py"
)


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
                if isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
            )
    return ()


def main() -> int:
    required = (
        CONTRACT,
        MIGRATION,
        DOMAIN,
        PORT,
        MEMORY,
        SERVICE,
        ACQUISITION,
        POSTGRES,
        PIPELINE,
        MAIN,
        MEMORY_TEST,
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
    domain = DOMAIN.read_text(encoding="utf-8")
    port = PORT.read_text(encoding="utf-8")
    memory = MEMORY.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    acquisition = ACQUISITION.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")

    schedule = contract.get("schedule", {})
    if schedule.get("cadence") != "UTC_FIXED_INTERVAL":
        problems.append("schedule cadence must remain UTC_FIXED_INTERVAL")
    if schedule.get("cron_supported") is not False:
        problems.append("cron must remain excluded")
    if schedule.get("configuration_immutable") is not True:
        problems.append("schedule configuration must remain immutable")
    planning = contract.get("planning", {})
    if planning.get("postgres_locking") != "FOR_UPDATE_SKIP_LOCKED":
        problems.append("planner PostgreSQL locking is not locked")
    if planning.get("next_due_basis") != "PREVIOUS_DUE_PLUS_INTERVAL":
        problems.append("next due time must derive from previous due time")
    if planning.get("execution_time_drift") is not False:
        problems.append("execution-time cadence drift must remain forbidden")
    dispatch = contract.get("dispatch", {})
    if dispatch.get("postgres_locking") != "FOR_UPDATE_SKIP_LOCKED":
        problems.append("dispatch PostgreSQL locking is not locked")
    if contract.get("composition", {}).get("continuous_loop") is not False:
        problems.append("continuous scheduler loop must remain excluded")

    result_fields = _dataclass_fields(service, "SourceDispatchExecutionResult")
    expected_result_fields = (
        "outcome",
        "worker_ref",
        "duration_ms",
        "schedule_id",
        "dispatch_id",
        "due_at",
        "attempt_count",
        "source_artifact_id",
        "ingestion_run_id",
        "error_code",
    )
    if result_fields != expected_result_fields:
        problems.append(
            "SourceDispatchExecutionResult allowlist drifted: "
            + ", ".join(result_fields)
        )

    _require(
        problems,
        "scheduler migration",
        migration,
        (
            'revision = "20260802_0022"',
            'down_revision = "20260802_0021"',
            "CREATE TABLE knowledge.source_acquisition_schedule",
            "CREATE TABLE knowledge.source_acquisition_dispatch",
            "UNIQUE(schedule_id, due_at)",
            "interval_seconds BETWEEN 60 AND 2592000",
            "max_dispatch_attempts BETWEEN 1 AND 10",
            "source_acquisition_schedule_due_idx",
            "source_acquisition_dispatch_pending_idx",
            "source_acquisition_dispatch_running_expiry_idx",
            "DROP TABLE IF EXISTS knowledge.source_acquisition_dispatch",
            "DROP TABLE IF EXISTS knowledge.source_acquisition_schedule",
        ),
    )
    _require(
        problems,
        "scheduler domain",
        domain,
        (
            "class SourceAcquisitionScheduleState(StrEnum):",
            "class SourceAcquisitionSchedule:",
            "def transition(",
            "def advance_after_planning(",
            "self.next_due_at + self.interval_delta",
            "class SourceAcquisitionDispatchState(StrEnum):",
            "class SourceAcquisitionDispatch:",
            "def claim(",
            "def heartbeat(",
            "def recover_stale(",
            "SOURCE_DISPATCH_ATTEMPTS_EXHAUSTED",
            "def complete(",
        ),
    )
    _require(
        problems,
        "scheduler port",
        port,
        (
            "class SourceAcquisitionSchedulerRepository(Protocol):",
            "def plan_due_once(",
            "def claim_pending_once(",
            "def heartbeat(",
            "def complete(",
            "def recover_stale(",
        ),
    )
    _require(
        problems,
        "memory scheduler",
        memory,
        (
            "with self._lock:",
            "selected.advance_after_planning(at=at)",
            "self._occurrences",
            "self._recover_stale_locked(at=claimed_at, limit=1000)",
            "dispatch.recover_stale(",
        ),
    )
    _require(
        problems,
        "PostgreSQL scheduler",
        postgres,
        (
            "FOR UPDATE SKIP LOCKED",
            "FOR UPDATE OF d SKIP LOCKED",
            "ON CONFLICT (schedule_key) DO NOTHING",
            "schedule.next_due_at\n                        + timedelta(seconds=schedule.interval_seconds)",
            "self._recover_stale(connection, at=claimed_at, limit=1000)",
        ),
    )
    if " OFFSET " in postgres.upper():
        problems.append("scheduler planner/dispatch selection may not use OFFSET")
    _require(
        problems,
        "acquisition persistence guards",
        acquisition,
        (
            "before_artifact_persist: Callable[[], None] | None = None",
            "before_run_admission: Callable[[], None] | None = None",
            "before_artifact_persist()",
            "before_run_admission()",
        ),
    )
    _require(
        problems,
        "scheduler service",
        service,
        (
            "class SourceAcquisitionSchedulerService:",
            "def plan_due_once(",
            "def execute_pending_once(",
            "before_artifact_persist=lambda: self._heartbeat(",
            "before_run_admission=lambda: self._heartbeat(",
            "self._heartbeat(claim, worker_ref=worker_ref, ttl_seconds=ttl_seconds)",
            "SourceDispatchExecutionOutcome.LEASE_LOST",
            "SourceDispatchExecutionOutcome.IDLE",
        ),
    )
    _require(
        problems,
        "composition",
        pipeline,
        (
            "InMemorySourceAcquisitionSchedulerRepository()",
            "PostgresSourceAcquisitionSchedulerRepository(engine)",
            "NoOpSourceDispatchObserver()",
            "SourceAcquisitionSchedulerService(",
            "source_scheduler_service=source_scheduler_service",
        ),
    )
    _require(
        problems,
        "application state",
        main_source,
        (
            "app.state.source_scheduler_repository",
            "app.state.source_dispatch_observer",
            "app.state.source_scheduler_service",
        ),
    )
    _require(
        problems,
        "memory evidence",
        memory_test,
        (
            "test_fixed_interval_planning_has_no_drift_and_lifecycle_is_explicit",
            "test_successful_dispatch_persists_only_artifact_and_run_identifiers",
            "test_exclusive_claim_owner_enforcement_stale_recovery_and_exhaustion",
            "test_lease_loss_before_artifact_persistence_produces_zero_writes",
            "test_lease_loss_before_run_admission_leaves_replayable_artifact",
            "test_crash_after_acquisition_replays_same_ids_and_completes_dispatch",
        ),
    )
    _require(
        problems,
        "PostgreSQL evidence",
        postgres_test,
        (
            "test_postgres_concurrent_planners_create_one_unique_occurrence_without_drift",
            "test_postgres_concurrent_executors_never_complete_same_dispatch_twice",
            "test_postgres_stale_dispatch_recovery_exhausts_bounded_attempts",
            "test_postgres_crash_after_acquisition_replays_same_ids_and_completes",
            "ThreadPoolExecutor",
            "Barrier(2)",
        ),
    )

    combined_domain = domain + port + memory + service
    forbidden_imports = tuple(
        fragment
        for fragment in (
            "from openai",
            "import openai",
            "import requests",
            "import httpx",
            "from google",
            "import tweepy",
            "import selenium",
            "import playwright",
        )
        if fragment in combined_domain
    )
    if forbidden_imports:
        problems.append(
            "provider/network dependency leaked into scheduler domain: "
            + ", ".join(forbidden_imports)
        )
    for forbidden_behavior in (
        "APIRouter",
        "while True",
        "crontab",
        "croniter",
        "zoneinfo",
        "ingestion_worker_runner",
        "review_proposal(",
        "materialize_accepted_proposal(",
    ):
        if forbidden_behavior in combined_domain:
            problems.append(
                f"excluded behavior leaked into scheduler domain: {forbidden_behavior}"
            )

    forbidden_result_fields = set(
        contract.get("observer", {}).get("forbidden_fields", ())
    )
    if forbidden_result_fields.intersection(result_fields):
        problems.append("forbidden sensitive fields entered dispatch result")

    if problems:
        print("Source acquisition scheduler contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Source acquisition scheduler contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
