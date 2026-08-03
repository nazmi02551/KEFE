from __future__ import annotations

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = (
    REPO_ROOT
    / "docs"
    / "contracts"
    / "provider-admission-control-slice43.v1.json"
)
MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260802_0024_source_provider_admission.py"
)
PUBLIC_MIGRATION = (
    REPO_ROOT
    / "services"
    / "api"
    / "migrations"
    / "versions"
    / "20260803_0025_public_provider_credential_mode.py"
)
KNOWLEDGE = (
    REPO_ROOT / "services" / "api" / "src" / "kefe_api" / "modules" / "knowledge"
)
IDENTITY = KNOWLEDGE / "source_identity.py"
DOMAIN = KNOWLEDGE / "provider_control.py"
PORT = KNOWLEDGE / "provider_control_ports.py"
MEMORY = KNOWLEDGE / "provider_control_memory.py"
SERVICE = KNOWLEDGE / "provider_control_service.py"
ACQUISITION = KNOWLEDGE / "source_acquisition.py"
PUBLIC_EXECUTION = KNOWLEDGE / "provider_public_execution.py"
POSTGRES = (
    REPO_ROOT
    / "services"
    / "api"
    / "src"
    / "kefe_api"
    / "infrastructure"
    / "postgres_source_provider_admission.py"
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
MEMORY_TEST = (
    REPO_ROOT
    / "services"
    / "api"
    / "tests"
    / "test_provider_admission_control.py"
)
POSTGRES_TEST = (
    REPO_ROOT
    / "services"
    / "api"
    / "tests"
    / "test_provider_admission_control_postgres.py"
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
                child.target.id
                for child in node.body
                if isinstance(child, ast.AnnAssign)
                and isinstance(child.target, ast.Name)
            )
    return ()


def main() -> int:
    required = (
        CONTRACT,
        MIGRATION,
        PUBLIC_MIGRATION,
        IDENTITY,
        DOMAIN,
        PORT,
        MEMORY,
        SERVICE,
        ACQUISITION,
        PUBLIC_EXECUTION,
        POSTGRES,
        PIPELINE,
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
    public_migration = PUBLIC_MIGRATION.read_text(encoding="utf-8")
    identity = IDENTITY.read_text(encoding="utf-8")
    domain = DOMAIN.read_text(encoding="utf-8")
    port = PORT.read_text(encoding="utf-8")
    memory = MEMORY.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")
    acquisition = ACQUISITION.read_text(encoding="utf-8")
    public_execution = PUBLIC_EXECUTION.read_text(encoding="utf-8")
    postgres = POSTGRES.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")

    capability = contract.get("capability", {})
    if capability.get("configuration_immutable") is not True:
        problems.append("provider capability configuration must remain immutable")
    if capability.get("credential_modes") != ["PUBLIC", "SECRET_REF"]:
        problems.append("provider credential modes must be exact PUBLIC and SECRET_REF")
    if capability.get("public_secret_reference", "missing") is not None:
        problems.append("PUBLIC provider capability must not contain secret_ref")
    if capability.get("secret_ref_mode_reference_only") is not True:
        problems.append("SECRET_REF mode must remain opaque-reference-only")
    if capability.get("secret_value_persisted") is not False:
        problems.append("provider secret values may not be persisted")
    quota = contract.get("quota", {})
    if quota.get("algorithm") != "FIXED_WINDOW":
        problems.append("provider quota algorithm must remain FIXED_WINDOW")
    if quota.get("transactional") is not True:
        problems.append("provider quota admission must remain transactional")
    circuit = contract.get("circuit", {})
    if circuit.get("single_half_open_probe") is not True:
        problems.append("single half-open probe is not locked")
    integration = contract.get("acquisition_integration", {})
    if integration.get("permit_before_adapter_capture") is not True:
        problems.append("provider permit must precede adapter capture")
    if integration.get("success_completion_before_artifact_persistence") is not True:
        problems.append("permit success must precede artifact persistence")
    if integration.get("permit_completion_failure") != "FAIL_CLOSED_NO_ARTIFACT":
        problems.append("permit completion uncertainty must fail closed")

    result_fields = _dataclass_fields(domain, "ProviderAdmissionResult")
    expected_fields = tuple(
        contract.get("operational_result", {}).get("allowed_fields", ())
    )
    if result_fields != expected_fields:
        problems.append(
            "ProviderAdmissionResult allowlist drifted: " + ", ".join(result_fields)
        )

    _require(
        problems,
        "source adapter identity",
        identity,
        (
            "def require_versioned_adapter_code(",
            "immutable versioned identifier ending in .vN",
        ),
    )
    _require(
        problems,
        "provider migration",
        migration,
        (
            'revision = "20260802_0024"',
            'down_revision = "20260802_0023"',
            "CREATE TABLE knowledge.source_provider_capability",
            "CREATE TABLE knowledge.source_provider_capture_permit",
            "source_provider_permit_active_expiry_idx",
            "source_provider_single_half_open_probe_idx",
            "state = 'ACTIVE' AND was_half_open_probe",
            "DROP TABLE IF EXISTS knowledge.source_provider_capture_permit",
            "DROP TABLE IF EXISTS knowledge.source_provider_capability",
        ),
    )
    _require(
        problems,
        "public credential migration",
        public_migration,
        (
            'revision = "20260803_0025"',
            'down_revision = "20260802_0024"',
            "ADD COLUMN credential_mode text NOT NULL DEFAULT 'SECRET_REF'",
            "ALTER COLUMN secret_ref DROP NOT NULL",
            "source_provider_credential_mode_ck",
            "source_provider_credential_binding_ck",
            "credential_mode = 'PUBLIC' AND secret_ref IS NULL",
            "credential_mode = 'SECRET_REF'",
            "cannot downgrade while PUBLIC provider capabilities exist",
            "ALTER COLUMN secret_ref SET NOT NULL",
            "DROP COLUMN credential_mode",
        ),
    )
    _require(
        problems,
        "provider domain",
        domain,
        (
            "def require_secret_reference(",
            "class ProviderCredentialMode(StrEnum):",
            'PUBLIC = "PUBLIC"',
            'SECRET_REF = "SECRET_REF"',
            "credential_mode: ProviderCredentialMode",
            "secret_ref: str | None",
            "PUBLIC provider capability cannot contain secret_ref",
            "SECRET_REF provider capability requires secret_ref",
            "class ProviderCapabilityLifecycle(StrEnum):",
            'RETIRED = "RETIRED"',
            "class ProviderCircuitState(StrEnum):",
            'HALF_OPEN = "HALF_OPEN"',
            "class SourceProviderCapability:",
            "def immutable_configuration(self)",
            "def roll_quota_window(",
            "def prepare_circuit_for_admission(",
            "def record_success(",
            "def record_failure(",
            "def retry_after_for_open_circuit(",
            "def retry_after_for_quota(",
            "class ProviderCapturePermit:",
            "def abandon(",
            'failure_code="SOURCE_PROVIDER_PERMIT_EXPIRED"',
            "class ProviderAdmissionResult:",
        ),
    )
    _require(
        problems,
        "provider repository port",
        port,
        (
            "class SourceProviderAdmissionRepository(Protocol):",
            "def create_or_get(",
            "def get_active_execution_context(",
            "def transition_lifecycle(",
            "def admit(",
            "def complete_success(",
            "def complete_failure(",
        ),
    )
    _require(
        problems,
        "memory provider control",
        memory,
        (
            "with self._lock:",
            "credential_mode=capability.credential_mode",
            "secret_ref=capability.secret_ref",
            "capability.roll_quota_window(at=at)",
            "capability.prepare_circuit_for_admission(at=at)",
            "self._recover_expired_locked(capability, at=at)",
            "SOURCE_PROVIDER_HALF_OPEN_PROBE_ACTIVE",
            "capability.count_admission(at=at)",
            "permit.abandon(at=at)",
        ),
    )
    _require(
        problems,
        "PostgreSQL provider control",
        postgres,
        (
            "credential_mode",
            "ProviderCredentialMode(row[\"credential_mode\"])",
            "FOR UPDATE",
            "FOR UPDATE SKIP LOCKED",
            "source_provider_capture_permit",
            "source_provider_capability",
            "capability.roll_quota_window(at=at)",
            "capability.prepare_circuit_for_admission(at=at)",
            "capability.count_admission(at=at)",
            "permit.abandon(at=at)",
        ),
    )
    if " OFFSET " in postgres.upper():
        problems.append("provider admission/recovery may not use OFFSET")

    _require(
        problems,
        "provider service",
        service,
        (
            "class SourceProviderAdmissionService:",
            "credential_mode: ProviderCredentialMode = ProviderCredentialMode.SECRET_REF",
            "def register(",
            "def admit_capture(",
            "ProviderAdmissionOutcome.RATE_LIMITED",
            "ProviderAdmissionOutcome.CIRCUIT_OPEN",
            "def complete_capture_success(",
            "def complete_capture_failure(",
        ),
    )
    _require(
        problems,
        "public provider execution",
        public_execution,
        (
            "class PublicSourceCaptureAdapter(Protocol):",
            "class InMemoryPublicSourceCaptureRegistry:",
            "class PermitBoundPublicCaptureExecutor:",
            "class CredentialModeRoutingProviderCaptureExecutor:",
            "ProviderCredentialMode.PUBLIC",
            "ProviderCredentialMode.SECRET_REF",
            "SOURCE_PROVIDER_CREDENTIAL_MODE_MISMATCH",
        ),
    )
    _require(
        problems,
        "Source Acquisition integration",
        acquisition,
        (
            "class SourceCaptureAdmissionDecision:",
            "class SourceCaptureAdmission(Protocol):",
            "admission: SourceCaptureAdmission | None = None",
            "self._admission.admit_capture(",
            "self._capture_executor.capture(",
            "self._admission.complete_capture_success(",
            "self._admission.complete_capture_failure(",
            "SOURCE_PROVIDER_PERMIT_COMPLETION_FAILED",
            "self._knowledge_repository.add_source_artifact(",
        ),
    )
    admit_position = acquisition.find("self._admission.admit_capture(")
    capture_position = acquisition.find("self._capture_executor.capture(")
    completion_position = acquisition.find(
        "self._admission.complete_capture_success("
    )
    artifact_position = acquisition.find(
        "self._knowledge_repository.add_source_artifact("
    )
    if not 0 <= admit_position < capture_position < completion_position < artifact_position:
        problems.append("provider admission/capture/persistence order drifted")

    _require(
        problems,
        "strict production composition",
        pipeline,
        (
            "InMemorySourceProviderAdmissionRepository()",
            "PostgresSourceProviderAdmissionRepository(engine)",
            "SourceProviderAdmissionService(",
            "RssAtomSubscriptionManifestRegistry()",
            "build_rss_atom_public_capture_registry(",
            "CredentialModeRoutingProviderCaptureExecutor(",
            "admission=provider_admission_service",
            "capture_executor=provider_capture_executor",
            "source_capture_registry: SourceCaptureRegistry = InMemorySourceCaptureRegistry()",
        ),
    )
    if "RssAtomSubscriptionManifest(" in pipeline:
        problems.append("strict production composition contains a concrete feed manifest")
    if "rss_atom_subscription_activation_service.activate(" in pipeline:
        problems.append("strict production composition auto-activates a provider")

    _require(
        problems,
        "memory/acquisition evidence",
        memory_test,
        (
            "test_secret_reference_and_lifecycle_are_explicit_and_immutable",
            "test_fixed_window_quota_returns_exact_retry_after_and_rolls",
            "test_failure_threshold_half_open_probe_and_success_close_circuit",
            "test_half_open_probe_failure_reopens_and_expired_permit_is_abandoned",
            "test_source_acquisition_requires_capability_and_closes_permit_before_write",
            "test_capture_failure_updates_circuit_and_completion_failure_writes_nothing",
        ),
    )
    _require(
        problems,
        "PostgreSQL evidence",
        postgres_test,
        (
            "test_postgres_concurrent_quota_admission_is_transactional",
            "test_postgres_half_open_allows_exactly_one_concurrent_probe",
            "test_postgres_expired_permit_is_abandoned_and_counts_as_failure",
            "test_postgres_permit_completion_requires_exact_adapter_and_active_ttl",
            "ThreadPoolExecutor",
            "Barrier(2)",
        ),
    )

    forbidden_runtime = (
        domain + port + memory + service + acquisition + public_execution
    )
    for fragment in (
        "import requests",
        "import httpx",
        "from openai",
        "import openai",
        "import tweepy",
        "import selenium",
        "import playwright",
        "APIRouter",
        "while True",
        "time.sleep",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "publish(",
    ):
        if fragment in forbidden_runtime:
            problems.append(
                f"provider/network/editorial behavior leaked into control plane: {fragment}"
            )

    forbidden_fields = set(
        contract.get("operational_result", {}).get("forbidden_fields", ())
    )
    if forbidden_fields.intersection(result_fields):
        problems.append("sensitive field entered provider operational result")

    if problems:
        print("Provider admission control contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Provider admission control contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
