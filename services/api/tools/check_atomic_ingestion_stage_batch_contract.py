from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs" / "contracts" / "atomic-ingestion-stage-batch-slice35.v1.json"
PACKAGE = (
    REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "ingestion_orchestration"
)
PORTS = PACKAGE / "ports.py"
SERVICE = PACKAGE / "service.py"
BATCH = PACKAGE / "batch.py"
MEMORY = PACKAGE / "in_memory.py"
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_ingestion_orchestration.py"
)
MEMORY_TEST = REPO_ROOT / "services" / "api" / "tests" / "test_ingestion_stage_batch.py"
POSTGRES_TEST = (
    REPO_ROOT / "services" / "api" / "tests" / "test_ingestion_orchestration_postgres.py"
)


def _method(source: str, name: str, next_name: str) -> str:
    start = source.find(f"    def {name}(")
    end = source.find(f"    def {next_name}(", start + 1)
    if start < 0 or end < 0:
        return ""
    return source[start:end]


def _require(
    problems: list[str],
    label: str,
    content: str,
    fragments: tuple[str, ...],
) -> None:
    for fragment in fragments:
        if fragment not in content:
            problems.append(f"{label} missing: {fragment}")


def main() -> int:
    required = (
        CONTRACT,
        PORTS,
        SERVICE,
        BATCH,
        MEMORY,
        POSTGRES,
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
    ports = PORTS.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    batch = BATCH.read_text(encoding="utf-8")
    memory = MEMORY.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")

    transaction = contract.get("transaction_boundary", {})
    if transaction.get("operation") != "complete_successful_stage":
        problems.append("atomic operation name is not locked")
    if transaction.get("partial_visibility_allowed") is not False:
        problems.append("partial visibility must be false")
    if transaction.get("memory_single_critical_section") is not True:
        problems.append("memory critical-section requirement is missing")
    if transaction.get("postgres_single_transaction") is not True:
        problems.append("PostgreSQL transaction requirement is missing")
    if transaction.get("schema_migration_required") is not False:
        problems.append("Slice 35 must not claim a schema migration")

    failure = contract.get("failure_semantics", {})
    for field in (
        "validation_before_memory_mutation",
        "postgres_rollback_on_any_error",
    ):
        if failure.get(field) is not True:
            problems.append(f"failure contract must keep {field}=true")
    for field in (
        "failed_completion_persists_success_stage",
        "failed_completion_persists_partial_proposals",
    ):
        if failure.get(field) is not False:
            problems.append(f"failure contract must keep {field}=false")

    _require(
        problems,
        "repository port",
        ports,
        (
            "def complete_successful_stage(",
            "execution: StageExecution",
            "proposals: tuple[Proposal, ...]",
        ),
    )
    _require(
        problems,
        "batch validator",
        batch,
        (
            "def order_successful_stage_batch(",
            "StageOutcome.SUCCEEDED",
            "proposal batch contains duplicate ids",
            "proposal batch contains another run",
            "proposal batch references another stage execution",
            "proposal supersession cycle detected",
        ),
    )
    _require(
        problems,
        "orchestration service",
        service,
        (
            "proposals = tuple(",
            "self._repository.complete_successful_stage(execution, proposals)",
        ),
    )

    success_section_start = service.find("        completed_at = utcnow()")
    success_section_end = service.find("        return execution", success_section_start)
    success_section = (
        service[success_section_start:success_section_end]
        if success_section_start >= 0 and success_section_end >= 0
        else ""
    )
    if not success_section:
        problems.append("successful service persistence section was not found")
    for forbidden in (
        "add_stage_execution(",
        "add_proposal(",
    ):
        if forbidden in success_section:
            problems.append("successful service path persists output one-by-one: " + forbidden)

    memory_method = _method(memory, "complete_successful_stage", "list_stage_executions")
    _require(
        problems,
        "memory atomic method",
        memory_method,
        (
            "with self._lock:",
            "order_successful_stage_batch(execution, proposals)",
            "run.state is not IngestionRunState.RUNNING",
            "execution_copy = deepcopy(execution)",
            "proposal_copies = tuple(",
        ),
    )
    first_memory_mutation = memory_method.find(
        "self._stage_executions[execution.id] = execution_copy"
    )
    last_memory_validation = memory_method.find(
        "proposal cannot supersede a proposal from another run"
    )
    if first_memory_mutation < 0 or first_memory_mutation < last_memory_validation:
        problems.append("memory mutation occurs before full batch validation")

    postgres_method = _method(postgres, "complete_successful_stage", "list_stage_executions")
    _require(
        problems,
        "PostgreSQL atomic method",
        postgres_method,
        (
            "with self._engine.begin() as connection:",
            "FOR UPDATE",
            "order_successful_stage_batch(execution, proposals)",
            "self._insert_stage_execution(connection, execution)",
            "self._insert_proposal(connection, proposal)",
            "except IntegrityError as exc:",
        ),
    )
    for forbidden in (
        "self.add_stage_execution(",
        "self.add_proposal(",
    ):
        if forbidden in postgres_method:
            problems.append(
                "PostgreSQL atomic method delegates to separate transactions: " + forbidden
            )

    _require(
        problems,
        "memory evidence",
        memory_test,
        (
            "test_service_uses_one_atomic_success_repository_call",
            "test_memory_invalid_batch_rolls_back_stage_and_all_proposals",
            "test_memory_orders_same_batch_supersession_and_rejects_cycles",
        ),
    )
    _require(
        problems,
        "PostgreSQL evidence",
        postgres_test,
        (
            "test_postgres_success_stage_batch_rolls_back_and_orders_supersession",
            "failed_stage_count == 0",
            "failed_proposal_count == 0",
            "success_stage_count == 1",
            "success_proposal_count == 2",
        ),
    )

    package_source = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.py"))
    provider_leaks = tuple(
        fragment
        for fragment in (
            "from openai",
            "import openai",
            "import requests",
            "import httpx",
            "from google",
            "import tweepy",
            "neo4j",
        )
        if fragment in package_source
    )
    if provider_leaks:
        problems.append(
            "provider dependency leaked into ingestion domain: " + ", ".join(provider_leaks)
        )

    if problems:
        print("Atomic ingestion stage batch contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Atomic ingestion stage batch contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
