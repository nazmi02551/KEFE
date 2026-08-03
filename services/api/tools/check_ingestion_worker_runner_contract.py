from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs" / "contracts" / "ingestion-worker-runner-slice38.v1.json"
PACKAGE = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "ingestion_orchestration"
)
RUNTIME = PACKAGE / "worker_runtime.py"
RUNNER = PACKAGE / "worker_service.py"
ORCHESTRATION = PACKAGE / "service.py"
LEASE_PORT = PACKAGE / "lease_ports.py"
LEASE_SERVICE = PACKAGE / "lease_service.py"
MEMORY_LEASES = PACKAGE / "in_memory_leases.py"
POSTGRES_LEASES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_ingestion_run_leases.py"
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
MEMORY_TEST = REPO_ROOT / "services" / "api" / "tests" / "test_ingestion_worker_runner.py"
POSTGRES_TEST = (
    REPO_ROOT
    / "services"
    / "api"
    / "tests"
    / "test_ingestion_worker_runner_postgres.py"
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


def main() -> int:
    required = (
        CONTRACT,
        RUNTIME,
        RUNNER,
        ORCHESTRATION,
        LEASE_PORT,
        LEASE_SERVICE,
        MEMORY_LEASES,
        POSTGRES_LEASES,
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
    runtime = RUNTIME.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    orchestration = ORCHESTRATION.read_text(encoding="utf-8")
    lease_port = LEASE_PORT.read_text(encoding="utf-8")
    lease_service = LEASE_SERVICE.read_text(encoding="utf-8")
    memory_leases = MEMORY_LEASES.read_text(encoding="utf-8")
    postgres_leases = POSTGRES_LEASES.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")

    if contract.get("runtime_plan", {}).get("selection") != "EXACT_ONLY":
        problems.append("runtime plan selection must remain EXACT_ONLY")
    if contract.get("claim", {}).get("pipeline_version_filter") is not True:
        problems.append("claim must filter exact pipeline version")
    supervision = contract.get("lease_supervision", {})
    if supervision.get("heartbeat_before_processor") is not True:
        problems.append("heartbeat-before-processor is not locked")
    if supervision.get("heartbeat_before_persistence") is not True:
        problems.append("heartbeat-before-persistence is not locked")
    if supervision.get("lease_loss_persists_stage_outcome") is not False:
        problems.append("lease loss must not persist stage outcome")
    if contract.get("completion", {}).get("automatic_retry_or_requeue") is not False:
        problems.append("automatic retry/requeue must remain excluded")

    _require(
        problems,
        "worker runtime",
        runtime,
        (
            "class IngestionRuntimeStage:",
            "class IngestionRuntimePlan:",
            "class InMemoryIngestionWorkerRuntimeRegistry:",
            "duplicate ingestion runtime plan identity",
            "every runtime plan stage requires an exact registered processor",
            "class IngestionWorkerRunOutcome(StrEnum):",
            "class IngestionWorkerRunResult:",
            "def as_operational_dict(",
            "class NoOpIngestionWorkerObserver:",
        ),
    )
    _require(
        problems,
        "worker runner",
        runner,
        (
            "class IngestionWorkerRunner:",
            "def run_once(",
            "pipeline_version=plan.pipeline_version",
            "self._heartbeat(",
            "before_persist=lambda: self._heartbeat(",
            "input_hash = run.input_content_hash",
            "input_hash = successful.output_hash",
            "self._orchestration.mark_succeeded(run.id)",
            "IngestionRunLeaseReleaseDisposition.TERMINAL",
            "IngestionWorkerRunOutcome.LEASE_LOST",
            "INGESTION_PIPELINE_HISTORY_INVALID",
        ),
    )
    _require(
        problems,
        "orchestration admission",
        orchestration,
        (
            "before_persist: Callable[[], None] | None = None",
            "self._admit_persistence(before_persist)",
            "def _admit_persistence(",
        ),
    )
    _require(
        problems,
        "lease exact plan filtering",
        lease_port + lease_service + memory_leases + postgres_leases,
        (
            "pipeline_version: str | None = None",
            "run.pipeline_version == pipeline_version",
            "r.pipeline_version = :pipeline_version",
        ),
    )
    _require(
        problems,
        "composition",
        pipeline,
        (
            "RssAtomSubscriptionManifestRegistry()",
            "build_rss_atom_ingestion_worker_registry(",
            "NoOpIngestionWorkerObserver()",
            "IngestionWorkerRunner(",
            "ingestion_worker_runner=ingestion_worker_runner",
        ),
    )
    if "RssAtomSubscriptionManifest(" in pipeline:
        problems.append("composition contains a concrete RSS/Atom subscription")
    if "rss_atom_subscription_activation_service.activate(" in pipeline:
        problems.append("composition auto-activates an ingestion pipeline")
    _require(
        problems,
        "application state",
        main_source,
        (
            "app.state.ingestion_worker_runtime_registry",
            "app.state.ingestion_worker_observer",
            "app.state.ingestion_worker_runner",
        ),
    )
    _require(
        problems,
        "memory evidence",
        memory_test,
        (
            "test_worker_claims_exact_pipeline_version_and_reports_idle",
            "test_worker_executes_hash_chained_plan_and_exposes_no_payload",
            "test_lease_loss_before_persistence_leaves_zero_stage_output",
            "test_crash_recovery_resumes_after_successful_stage_without_reexecution",
            "test_retryable_and_final_failures_release_without_automatic_requeue",
            "test_empty_registry_blocks_without_claiming_work",
        ),
    )
    _require(
        problems,
        "PostgreSQL evidence",
        postgres_test,
        (
            "test_postgres_worker_claim_filters_exact_pipeline_version",
            "test_postgres_worker_crash_recovery_resumes_after_successful_stage",
        ),
    )

    domain_source = runtime + runner
    forbidden = tuple(
        fragment
        for fragment in (
            "from openai",
            "import openai",
            "import requests",
            "import httpx",
            "from google",
            "import tweepy",
            "APIRouter",
            "provider_response",
            "proposal_payload\":",
            "private_reason\":",
            "exception_text\":",
        )
        if fragment in domain_source
    )
    if forbidden:
        problems.append(
            "provider/HTTP/sensitive payload leaked into worker domain: "
            + ", ".join(forbidden)
        )
    for forbidden_runtime_fragment in (
        "while True",
        "schedule.",
        "cron",
        "auto_project",
        "review_proposal(",
        "materialize_accepted_proposal(",
    ):
        if forbidden_runtime_fragment in runner:
            problems.append(
                f"excluded autonomous behavior in worker runner: {forbidden_runtime_fragment}"
            )

    if problems:
        print("Ingestion worker runner contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Ingestion worker runner contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
