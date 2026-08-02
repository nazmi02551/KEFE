from __future__ import annotations

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "source-acquisition-admission-slice39.v1.json"
)
SOURCE = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "modules"
    / "knowledge"
    / "source_acquisition.py"
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
MEMORY_TEST = REPO_ROOT / "services" / "api" / "tests" / "test_source_acquisition.py"
POSTGRES_TEST = (
    REPO_ROOT
    / "services"
    / "api"
    / "tests"
    / "test_source_acquisition_postgres.py"
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
    required = (CONTRACT, SOURCE, PIPELINE, MAIN, MEMORY_TEST, POSTGRES_TEST)
    missing = [path for path in required if not path.exists()]
    if missing:
        for path in missing:
            print(f"missing required file: {path.relative_to(REPO_ROOT)}")
        return 1

    problems: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = SOURCE.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")

    adapter_identity = contract.get("adapter_identity", {})
    if adapter_identity.get("selection") != "EXACT_ONLY":
        problems.append("source adapter selection must remain EXACT_ONLY")
    if adapter_identity.get("immutable_semantics") is not True:
        problems.append("source adapter identity must remain immutable")
    if adapter_identity.get("duplicate_registration_rejected") is not True:
        problems.append("duplicate source adapter registration must be rejected")
    if contract.get("artifact", {}).get("aggregate") != "SourceArtifact":
        problems.append("source acquisition must reuse SourceArtifact")
    if contract.get("run_admission", {}).get("aggregate") != "IngestionRun":
        problems.append("source acquisition must reuse IngestionRun")
    if contract.get("recovery", {}).get("artifact_compensation_delete") is not False:
        problems.append("artifact compensation delete must remain forbidden")
    if contract.get("composition", {}).get("default_registry") != "EMPTY":
        problems.append("production source adapter registry must remain empty")

    captured_fields = _dataclass_fields(source, "CapturedSource")
    expected_captured = (
        "content_hash",
        "external_id",
        "canonical_url",
        "publisher_or_issuer",
        "published_at",
        "language_code",
        "jurisdiction_code",
        "raw_storage_ref",
    )
    if captured_fields != expected_captured:
        problems.append(
            "CapturedSource field allowlist drifted: " + ", ".join(captured_fields)
        )

    result_fields = _dataclass_fields(source, "SourceAcquisitionResult")
    expected_result = (
        "outcome",
        "adapter_code",
        "pipeline_code",
        "pipeline_version",
        "trace_id",
        "duration_ms",
        "source_artifact_id",
        "ingestion_run_id",
        "error_code",
    )
    if result_fields != expected_result:
        problems.append(
            "SourceAcquisitionResult field allowlist drifted: "
            + ", ".join(result_fields)
        )

    _require(
        problems,
        "source acquisition domain",
        source,
        (
            "def require_versioned_adapter_code(",
            "class CapturedSource:",
            "class RetryableSourceCaptureError(Exception):",
            "class FinalSourceCaptureError(Exception):",
            "class SourceCaptureAdapter(Protocol):",
            "class InMemorySourceCaptureRegistry:",
            "duplicate source capture adapter code",
            "class SourceAcquisitionCommand:",
            "class SourceAcquisitionResult:",
            "class SourceAcquisitionService:",
            "SourceArtifact.create(",
            "self._knowledge_repository.add_source_artifact(",
            "InputArtifactKind.SOURCE_ARTIFACT",
            "self._ingestion_service.start_run(",
            "SOURCE_CAPTURE_ADAPTER_NOT_REGISTERED",
            "UNEXPECTED_SOURCE_CAPTURE_FAILURE",
            "SOURCE_ACQUISITION_ADMISSION_RETRYABLE",
            "except Exception:\n            pass",
        ),
    )
    _require(
        problems,
        "source acquisition composition",
        pipeline,
        (
            "InMemorySourceCaptureRegistry()",
            "NoOpSourceAcquisitionObserver()",
            "SourceAcquisitionService(",
            "knowledge_repository=knowledge_repository",
            "source_acquisition_service=source_acquisition_service",
        ),
    )
    _require(
        problems,
        "application state",
        main_source,
        (
            "app.state.knowledge_repository",
            "app.state.source_capture_registry",
            "app.state.source_acquisition_observer",
            "app.state.source_acquisition_service",
        ),
    )
    _require(
        problems,
        "memory evidence",
        memory_test,
        (
            "test_versioned_adapter_validation_and_duplicate_rejection",
            "test_unchanged_capture_replays_same_artifact_and_run_without_payload_leak",
            "test_changed_content_hash_creates_new_artifact_and_run",
            "test_preexisting_artifact_without_run_is_completed_by_replay",
            "test_capture_failures_and_missing_adapter_produce_zero_writes",
            "test_observer_failure_does_not_change_admission_result",
        ),
    )
    _require(
        problems,
        "PostgreSQL evidence",
        postgres_test,
        (
            "test_postgres_unchanged_capture_reuses_artifact_and_run_identity",
            "test_postgres_changed_hash_creates_new_immutable_artifact_and_run",
            "test_postgres_preexisting_artifact_without_run_is_completed_by_replay",
        ),
    )

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
        if fragment in source
    )
    if forbidden_imports:
        problems.append(
            "provider/network dependency leaked into source acquisition domain: "
            + ", ".join(forbidden_imports)
        )
    for forbidden_behavior in (
        "APIRouter",
        ".normalize(",
        "ingestion_worker_runner",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "while True",
        "schedule.",
        "cron",
    ):
        if forbidden_behavior in source:
            problems.append(
                f"excluded behavior leaked into source acquisition: {forbidden_behavior}"
            )

    forbidden_capture_fields = set(
        contract.get("capture_envelope", {}).get("forbidden_fields", ())
    )
    if forbidden_capture_fields.intersection(captured_fields):
        problems.append("forbidden raw/provider fields entered CapturedSource")
    forbidden_result_fields = set(
        contract.get("observer", {}).get("forbidden_fields", ())
    )
    if forbidden_result_fields.intersection(result_fields):
        problems.append("forbidden sensitive fields entered acquisition result")

    if problems:
        print("Source acquisition admission contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Source acquisition admission contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
