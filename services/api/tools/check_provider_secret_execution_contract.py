from __future__ import annotations

import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT = REPO_ROOT / "docs/contracts/provider-secret-execution-slice44.v1.json"
ADR = REPO_ROOT / "docs/adr/0080-ephemeral-secret-resolution-and-secure-provider-invocation.md"
EXECUTION = REPO_ROOT / "services/api/src/kefe_api/modules/knowledge/provider_secret_execution.py"
CONTEXT = REPO_ROOT / "services/api/src/kefe_api/modules/knowledge/provider_execution_context.py"
POSTGRES_CONTEXT = (
    REPO_ROOT / "services/api/src/kefe_api/infrastructure/postgres_provider_execution_context.py"
)
SOURCE = REPO_ROOT / "services/api/src/kefe_api/modules/knowledge/source_acquisition.py"
PIPELINE = REPO_ROOT / "services/api/src/kefe_api/infrastructure/editorial_pipeline.py"
MEMORY_TEST = REPO_ROOT / "services/api/tests/test_provider_secret_execution.py"
POSTGRES_TEST = REPO_ROOT / "services/api/tests/test_provider_secret_execution_postgres.py"
PUBLIC_TEST = REPO_ROOT / "services/api/tests/test_public_provider_capture.py"


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
        ADR,
        EXECUTION,
        CONTEXT,
        POSTGRES_CONTEXT,
        SOURCE,
        PIPELINE,
        MEMORY_TEST,
        POSTGRES_TEST,
        PUBLIC_TEST,
    )
    missing = [path for path in required if not path.exists()]
    if missing:
        for path in missing:
            print(f"missing required file: {path.relative_to(REPO_ROOT)}")
        return 1

    problems: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    execution = EXECUTION.read_text(encoding="utf-8")
    context = CONTEXT.read_text(encoding="utf-8")
    postgres_context = POSTGRES_CONTEXT.read_text(encoding="utf-8")
    source = SOURCE.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    memory_test = MEMORY_TEST.read_text(encoding="utf-8")
    postgres_test = POSTGRES_TEST.read_text(encoding="utf-8")
    public_test = PUBLIC_TEST.read_text(encoding="utf-8")

    lease = contract.get("secret_lease", {})
    if lease.get("access") != "CALLBACK_SCOPED_BYTES":
        problems.append("secret access must remain callback scoped")
    if lease.get("zeroize_on_close") is not True:
        problems.append("secret lease must remain zeroized on close")
    if lease.get("close_in_finally") is not True:
        problems.append("secret lease must remain closed in finally")
    if lease.get("value_return_api") is not False:
        problems.append("secret value return API must remain forbidden")
    if contract.get("resolver_registry", {}).get("selection") != "EXACT_SCHEME_ONLY":
        problems.append("resolver selection must remain exact by scheme")
    if contract.get("resolver_registry", {}).get("fallback") is not False:
        problems.append("resolver fallback must remain forbidden")
    if contract.get("adapter_registry", {}).get("default_registry") != "EMPTY":
        problems.append("credential-aware adapter registry must default empty")
    permit_contract = contract.get("permit_context", {})
    if permit_contract.get("required_credential_mode") != "SECRET_REF":
        problems.append("secret execution must require SECRET_REF mode")
    if permit_contract.get("public_rejected_before_resolver_lookup") is not True:
        problems.append("PUBLIC mode must be rejected before resolver lookup")
    if contract.get("production_composition", {}).get("network") is not False:
        problems.append("network must remain excluded")
    if contract.get("production_composition", {}).get("provider_adapter") is not False:
        problems.append("real provider adapter must remain excluded")
    if (
        contract.get("production_composition", {}).get("source_capture_path")
        != "CREDENTIAL_MODE_ROUTER"
    ):
        problems.append("source capture must enter through credential-mode router")

    context_fields = _dataclass_fields(context, "ProviderPermitExecutionContext")
    expected_context_fields = (
        "permit_id",
        "adapter_code",
        "secret_ref",
        "permit_expires_at",
        "credential_mode",
    )
    if context_fields != expected_context_fields:
        problems.append("permit context field allowlist drifted: " + ", ".join(context_fields))

    _require(
        problems,
        "secret execution",
        execution,
        (
            "class SecretAccess(Protocol):",
            "class SecretLease:",
            '__slots__ = ("_material", "_expires_at", "_closed")',
            "__hash__ = None",
            "def use_bytes(",
            "memoryview(self._material).toreadonly()",
            "def close(self) -> None:",
            "self._material[index] = 0",
            "SecretLease comparison is forbidden",
            "SecretLease serialization is forbidden",
            "class InMemorySecretResolverRegistry:",
            "urlsplit(secret_ref).scheme.lower()",
            "class InMemoryCredentialAwareSourceCaptureRegistry:",
            "class SecureProviderCaptureExecutor:",
            "get_active_execution_context(",
            "context.credential_mode is not ProviderCredentialMode.SECRET_REF",
            "SOURCE_PROVIDER_CREDENTIAL_MODE_MISMATCH",
            "resolver.resolve(",
            "adapter.capture(",
            "finally:\n            lease.close()",
            "SOURCE_SECRET_RESOLVER_NOT_REGISTERED",
            "SOURCE_SECRET_RESOLUTION_RETRYABLE",
            "SOURCE_SECRET_RESOLUTION_FINAL",
            "SOURCE_SECRET_RESOLUTION_UNEXPECTED",
            "SOURCE_CREDENTIAL_ADAPTER_NOT_REGISTERED",
        ),
    )
    mode_position = execution.find(
        "context.credential_mode is not ProviderCredentialMode.SECRET_REF"
    )
    resolver_position = execution.find("self._resolvers.get_for_reference(secret_ref)")
    if not 0 <= mode_position < resolver_position:
        problems.append("PUBLIC mode is not rejected before resolver selection")

    _require(
        problems,
        "permit context",
        context,
        (
            "secret_ref: str | None = field(repr=False)",
            "credential_mode: ProviderCredentialMode",
            "PUBLIC permit context cannot contain secret_ref",
            "SECRET_REF permit context requires secret_ref",
            "secret_ref=<REDACTED>",
            "class ProviderPermitContextError(Exception):",
            "SOURCE_PROVIDER_PERMIT_CONTEXT_INVALID",
        ),
    )
    _require(
        problems,
        "PostgreSQL permit context",
        postgres_context,
        (
            'isolation_level="REPEATABLE READ"',
            "SET TRANSACTION READ ONLY",
            "capability.credential_mode",
            'ProviderCredentialMode(row["credential_mode"])',
            "permit.id = :permit_id",
            "permit.adapter_code = :adapter_code",
            "permit.state = 'ACTIVE'",
            "permit.expires_at > :at",
            "capability.lifecycle_state = 'ENABLED'",
        ),
    )
    _require(
        problems,
        "source acquisition integration",
        source,
        (
            "class SourceCaptureExecutor(Protocol):",
            "capture_executor: SourceCaptureExecutor | None = None",
            "self._capture_executor = capture_executor",
            "self._capture_executor.capture(",
            "permit_id=permit_id",
            "self._admission.complete_capture_success(",
            "self._knowledge_repository.add_source_artifact(",
        ),
    )
    capture_index = source.find("self._capture_executor.capture(")
    completion_index = source.find("self._admission.complete_capture_success(")
    persistence_index = source.find("self._knowledge_repository.add_source_artifact(")
    if not 0 <= capture_index < completion_index < persistence_index:
        problems.append("secure capture, permit completion and artifact persistence order drifted")

    _require(
        problems,
        "production composition",
        pipeline,
        (
            "InMemorySecretResolverRegistry()",
            "InMemoryCredentialAwareSourceCaptureRegistry()",
            "SecureProviderCaptureExecutor(",
            "PostgresProviderPermitExecutionContextRepository(",
            "provider_execution_context_repository =",
            "engine",
            "contexts=provider_execution_context_repository",
            "CredentialModeRoutingProviderCaptureExecutor(",
            "credentialed_executor=secure_provider_capture_executor",
            "capture_executor=provider_capture_executor",
        ),
    )
    _require(
        problems,
        "memory evidence",
        memory_test,
        (
            "test_secret_lease_redacts_forbids_serialization_and_zeroizes",
            "test_secret_lease_rejects_expiry_and_context_repr_redacts_reference",
            "test_secure_executor_uses_exact_registries_and_zeroizes_after_success",
            "test_secure_executor_zeroizes_after_adapter_or_resolution_failure",
            "test_secure_source_acquisition_completes_permit_before_persistence",
            "test_resolution_failure_closes_permit_and_writes_nothing",
            "test_empty_production_style_registries_fail_closed",
        ),
    )
    _require(
        problems,
        "public mode rejection evidence",
        public_test,
        (
            "test_public_and_credentialed_executors_reject_cross_mode_before_side_effects",
            "resolver_spy.called is False",
        ),
    )
    _require(
        problems,
        "PostgreSQL evidence",
        postgres_test,
        (
            "test_postgres_execution_context_requires_exact_active_unexpired_permit",
            "test_postgres_paused_capability_cannot_resolve_active_permit_context",
        ),
    )

    combined = "\n".join((execution, context, postgres_context, pipeline))
    for forbidden in (
        "import requests",
        "import httpx",
        "from boto",
        "import boto",
        "from google.cloud",
        "from azure",
        "os.environ",
        "os.getenv",
        "subprocess",
        "socket",
        "APIRouter",
        "while True",
        "sleep(",
    ):
        if forbidden in combined:
            problems.append(f"excluded dependency/behavior leaked: {forbidden}")

    result_fields = _dataclass_fields(source, "SourceAcquisitionResult")
    forbidden_result_fields = set(contract.get("privacy_allowlist", {}).get("forbidden_fields", ()))
    if forbidden_result_fields.intersection(result_fields):
        problems.append("secret/provider fields entered SourceAcquisitionResult")

    if problems:
        print("Provider secret execution contract check FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("Provider secret execution contract check PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
