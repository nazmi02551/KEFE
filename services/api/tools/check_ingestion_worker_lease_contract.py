from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs" / "contracts" / "ingestion-worker-lease-slice37.v1.json"
MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260802_0021_ingestion_run_lease.py"
)
PACKAGE = (
    REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "ingestion_orchestration"
)
MODELS = PACKAGE / "models.py"
LEASES = PACKAGE / "leases.py"
PORT = PACKAGE / "lease_ports.py"
SERVICE = PACKAGE / "lease_service.py"
MEMORY = PACKAGE / "in_memory_leases.py"
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_ingestion_run_leases.py"
)
PIPELINE = (
    REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "infrastructure" / "editorial_pipeline.py"
)
MAIN = REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "main.py"
MEMORY_TEST = REPO_ROOT / "services" / "api" / "tests" / "test_ingestion_run_leases.py"
POSTGRES_TEST = REPO_ROOT / "services" / "api" / "tests" / "test_ingestion_run_leases_postgres.py"


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
        MIGRATION,
        MODELS,
        LEASES,
        PORT,
        SERVICE,
        MEMORY,
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
    models = MODELS.read_text(encoding="utf-8")
    leases = LEASES.read_text(encoding="utf-8")
    port = PORT.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    memory = MEMORY.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")

    lease_model = contract.get("lease_model", {})
    if lease_model.get("states") != ["ACTIVE", "RELEASED", "EXPIRED"]:
        problems.append("lease states/order are not locked")
    if lease_model.get("one_active_lease_per_run") is not True:
        problems.append("one-active-lease invariant is not locked")
    if lease_model.get("minimum_ttl_seconds") != 5:
        problems.append("minimum lease TTL must remain 5 seconds")
    if lease_model.get("maximum_ttl_seconds") != 900:
        problems.append("maximum lease TTL must remain 900 seconds")
    claim = contract.get("claim", {})
    if claim.get("postgres_locking") != "FOR_UPDATE_SKIP_LOCKED":
        problems.append("PostgreSQL claim locking is not locked")
    if claim.get("recover_expired_before_select") is not True:
        problems.append("claim must recover expired leases first")
    if contract.get("recovery", {}).get("reclaim_uses_new_lease_id") is not True:
        problems.append("reclaim must use a new lease ID")

    _require(
        problems,
        "lease migration",
        migration,
        (
            'revision = "20260802_0021"',
            'down_revision = "20260802_0020"',
            "CREATE TABLE ingestion.run_lease",
            "state IN ('ACTIVE','RELEASED','EXPIRED')",
            "run_lease_one_active_per_run_idx",
            "WHERE state = 'ACTIVE'",
            "run_lease_active_expiry_idx",
            "DROP TABLE IF EXISTS ingestion.run_lease",
        ),
    )
    _require(
        problems,
        "ingestion run state machine",
        models,
        (
            "IngestionRunState.RUNNING: frozenset(",
            "IngestionRunState.QUEUED,",
        ),
    )
    _require(
        problems,
        "lease domain",
        leases,
        (
            "class IngestionRunLeaseState(StrEnum):",
            "class IngestionRunLeaseReleaseDisposition(StrEnum):",
            "class IngestionRunLease:",
            "def is_active_at(",
            "def heartbeat(",
            "def release(",
            "def expire(",
            "class IngestionRunLeaseClaim:",
        ),
    )
    _require(
        problems,
        "lease port",
        port,
        (
            "class IngestionRunLeaseRepository(Protocol):",
            "def claim_next(",
            "def heartbeat(",
            "def assert_active(",
            "def release(",
            "def recover_expired(",
        ),
    )
    _require(
        problems,
        "lease service",
        service,
        (
            "MINIMUM_LEASE_TTL_SECONDS = 5",
            "MAXIMUM_LEASE_TTL_SECONDS = 900",
            "class IngestionRunLeaseService:",
            "self._repository.claim_next(",
            "self._repository.assert_active(",
            "self._repository.recover_expired(",
        ),
    )
    _require(
        problems,
        "memory lease repository",
        memory,
        (
            "with self._ingestion._lock:",
            "self._recover_expired_locked(at=claimed_at, limit=1000)",
            "key=lambda run: (run.updated_at, str(run.id))",
            "selected.transition(IngestionRunState.RUNNING",
            "run.transition(IngestionRunState.QUEUED",
            "self._active_by_run",
        ),
    )
    _require(
        problems,
        "PostgreSQL lease repository",
        postgres,
        (
            "FOR UPDATE SKIP LOCKED LIMIT 1",
            "ORDER BY r.updated_at ASC, r.id ASC",
            "self._recover_expired(connection, at=claimed_at, limit=1000)",
            "UPDATE ingestion.run_lease",
            "SET state = 'EXPIRED', released_at = :at",
            "SET state = 'QUEUED', updated_at = :at",
            "lease.worker_ref != worker_ref",
        ),
    )
    if " OFFSET " in postgres.upper():
        problems.append("lease claim may not use OFFSET")
    _require(
        problems,
        "composition",
        pipeline,
        (
            "InMemoryIngestionRunLeaseRepository(memory_ingestion)",
            "PostgresIngestionRunLeaseRepository(engine)",
            "IngestionRunLeaseService(ingestion_lease_repository)",
        ),
    )
    _require(
        problems,
        "application state",
        main_source,
        (
            "app.state.ingestion_run_lease_repository",
            "app.state.ingestion_run_lease_service",
        ),
    )
    _require(
        problems,
        "memory evidence",
        memory_test,
        (
            "test_memory_claim_is_oldest_first_exclusive_and_pipeline_filtered",
            "test_memory_heartbeat_requires_exact_owner_and_extends_expiry",
            "test_memory_expiry_requeues_and_reclaim_uses_new_lease",
            "test_memory_release_disposition_enforces_run_state",
        ),
    )
    _require(
        problems,
        "PostgreSQL evidence",
        postgres_test,
        (
            "test_postgres_concurrent_claimers_never_receive_same_run",
            "test_postgres_heartbeat_expiry_recovery_and_reclaim",
            "test_postgres_release_rules_requeue_and_terminal_history",
            "ThreadPoolExecutor",
            "Barrier(2)",
        ),
    )

    package_source = "\n".join(path.read_text(encoding="utf-8") for path in PACKAGE.glob("*.py"))
    leaks = tuple(
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
    if leaks:
        problems.append(
            "provider dependency leaked into ingestion lease domain: " + ", ".join(leaks)
        )
    if "APIRouter" in leases + port + service + memory:
        problems.append("Admin/HTTP concerns leaked into lease domain")

    if problems:
        print("Ingestion worker lease contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Ingestion worker lease contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
