from __future__ import annotations

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "content-supply-health-snapshot-slice42.v1.json"
)
MODULE = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "content_supply_health"
)
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
    / "postgres_content_supply_health.py"
)
CLI = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "run_content_supply_health_snapshot.py"
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
    REPO_ROOT / "services" / "api" / "tests" / "test_content_supply_health.py"
)
CLI_TEST = (
    REPO_ROOT
    / "services"
    / "api"
    / "tests"
    / "test_content_supply_health_cli.py"
)
POSTGRES_TEST = (
    REPO_ROOT
    / "services"
    / "api"
    / "tests"
    / "test_content_supply_health_postgres.py"
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


def _class_methods(source: str, class_name: str) -> tuple[str, ...]:
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return tuple(
                child.name
                for child in node.body
                if isinstance(child, ast.FunctionDef)
            )
    return ()


def _dataclass_fields(source: str, class_name: str) -> tuple[str, ...]:
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return tuple(
                child.target.id
                for child in node.body
                if isinstance(child, ast.AnnAssign)
                and isinstance(child.target, ast.Name)
            )
    return ()


def main() -> int:
    required = (
        CONTRACT,
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

    policy = contract.get("policy", {})
    if policy.get("immutable") is not True:
        problems.append("health policy must remain immutable")
    if policy.get("thresholds_are_slos") is not False:
        problems.append("health thresholds may not be labeled as SLOs")
    facts = contract.get("facts", {})
    if facts.get("mutation_allowed") is not False:
        problems.append("operational facts repository must remain read-only")
    if facts.get("postgres_consistency") != "REPEATABLE_READ":
        problems.append("PostgreSQL snapshot consistency is not locked")
    signals = contract.get("signals", {})
    if signals.get("automatic_recovery") is not False:
        problems.append("health snapshot may not recover durable work")

    port_methods = _class_methods(
        ports,
        "ContentSupplyOperationalFactsRepository",
    )
    if port_methods != ("read_facts",):
        problems.append(
            "health repository port must expose read_facts only: "
            + ", ".join(port_methods)
        )

    snapshot_fields = _dataclass_fields(models, "ContentSupplyHealthSnapshot")
    expected_fields = tuple(contract.get("snapshot", {}).get("allowed_fields", ()))
    if snapshot_fields != expected_fields:
        problems.append(
            "ContentSupplyHealthSnapshot allowlist drifted: "
            + ", ".join(snapshot_fields)
        )

    _require(
        problems,
        "health models",
        models,
        (
            "class ContentSupplyHealthPolicy:",
            "class ContentSupplyOperationalFacts:",
            "class ContentSupplyHealthSignal(StrEnum):",
            'QUIET = "QUIET"',
            'NOMINAL = "NOMINAL"',
            'ATTENTION = "ATTENTION"',
            'CRITICAL = "CRITICAL"',
            "class ContentSupplyHealthReason(StrEnum):",
            "class ContentSupplyHealthSnapshot:",
            "reason_codes must be sorted and unique",
        ),
    )
    _require(
        problems,
        "memory snapshot",
        memory,
        (
            "with self._scheduler._lock:",
            "with self._ingestion._lock:",
            "with self._cycles._lock:",
            "reviewed_proposal_ids",
            "latest_terminal",
            "ContentSupplyOperationalFacts(",
        ),
    )
    _require(
        problems,
        "PostgreSQL snapshot",
        postgres,
        (
            'isolation_level="REPEATABLE READ"',
            'text("SET TRANSACTION READ ONLY")',
            "source_acquisition_schedule",
            "source_acquisition_dispatch",
            "ingestion.ingestion_run",
            "ingestion.run_lease",
            "ingestion.proposal_review_decision",
            "ingestion.content_supply_cycle",
            "latest_terminal_cycle_state",
            "latest_terminal_cycle_completed_at",
        ),
    )
    upper_postgres = postgres.upper()
    for mutation in (" INSERT ", " UPDATE ", " DELETE ", " FOR UPDATE"):
        if mutation in upper_postgres:
            problems.append(
                f"mutation/locking leaked into PostgreSQL health snapshot: {mutation.strip()}"
            )

    _require(
        problems,
        "health service",
        service,
        (
            "class ContentSupplyHealthService:",
            "def snapshot(",
            "ContentSupplyHealthSignal.CRITICAL",
            "ContentSupplyHealthSignal.ATTENTION",
            "ContentSupplyHealthSignal.QUIET",
            "ContentSupplyHealthSignal.NOMINAL",
            "STALE_SOURCE_DISPATCH",
            "STALE_INGESTION_LEASE",
            "STALE_CONTENT_SUPPLY_CYCLE",
            "CONTENT_SUPPLY_CYCLE_SILENT",
            "tuple(sorted(reasons))",
        ),
    )
    _require(
        problems,
        "health CLI",
        cli,
        (
            "def parse_utc_datetime(",
            "def exit_code_for(",
            "return 2",
            "return 3",
            "INVALID_INPUT_EXIT_CODE = 64",
            "snapshot.as_operational_dict()",
            "content_supply_health_service.snapshot(",
        ),
    )
    _require(
        problems,
        "composition",
        pipeline,
        (
            "InMemoryContentSupplyOperationalFactsRepository(",
            "PostgresContentSupplyOperationalFactsRepository(engine)",
            "ContentSupplyHealthService(",
            "content_supply_health_service=content_supply_health_service",
        ),
    )
    _require(
        problems,
        "application state",
        main_source,
        (
            "app.state.content_supply_health_repository",
            "app.state.content_supply_health_service",
        ),
    )
    _require(
        problems,
        "memory/service evidence",
        memory_test,
        (
            "test_quiet_and_nominal_signals_are_distinct",
            "test_attention_reasons_are_explicit_sorted_and_threshold_driven",
            "test_running_cycle_suppresses_cycle_silence_attention",
            "test_any_stale_ownership_signal_is_critical",
            "test_snapshot_operational_allowlist_is_exact",
            "test_memory_repository_reads_live_aggregate_counts",
        ),
    )
    _require(
        problems,
        "CLI evidence",
        cli_test,
        (
            "test_cli_invokes_snapshot_with_explicit_policy_and_prints_allowlist",
            "test_cli_exit_codes_are_deterministic",
            "test_cli_invalid_policy_returns_usage_exit_without_service_call",
        ),
    )
    _require(
        problems,
        "PostgreSQL evidence",
        postgres_test,
        (
            "test_postgres_snapshot_reads_repeatable_aggregate_deltas_without_mutation",
            "baseline = facts_repository.read_facts",
            "assert snapshot.signal is ContentSupplyHealthSignal.CRITICAL",
            'assert dispatch_state == "RUNNING"',
            'assert cycle_state == "RUNNING"',
        ),
    )

    combined_runtime = models + ports + memory + service + postgres + cli
    forbidden_fragments = (
        "APIRouter",
        "while True",
        "time.sleep",
        "recover_stale(",
        "claim_pending_once(",
        "claim_next(",
        "heartbeat(",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "publish(",
        "import requests",
        "import httpx",
        "from openai",
        "import openai",
    )
    for fragment in forbidden_fragments:
        if fragment in combined_runtime:
            problems.append(
                f"excluded mutation/provider behavior leaked into health runtime: {fragment}"
            )

    forbidden_fields = set(contract.get("snapshot", {}).get("forbidden_fields", ()))
    if forbidden_fields.intersection(snapshot_fields):
        problems.append("forbidden sensitive field entered health snapshot")

    if problems:
        print("Content supply health snapshot contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Content supply health snapshot contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
