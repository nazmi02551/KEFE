from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
DOMAIN = API / "src/kefe_api/modules/knowledge/provider_control.py"
CONTEXT = API / "src/kefe_api/modules/knowledge/provider_execution_context.py"
MEMORY = API / "src/kefe_api/modules/knowledge/provider_control_memory.py"
SECRET_EXECUTION = API / "src/kefe_api/modules/knowledge/provider_secret_execution.py"
PUBLIC_EXECUTION = API / "src/kefe_api/modules/knowledge/provider_public_execution.py"
POSTGRES_ADMISSION = API / "src/kefe_api/infrastructure/postgres_source_provider_admission.py"
POSTGRES_CONTEXT = API / "src/kefe_api/infrastructure/postgres_provider_execution_context.py"
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
MAIN = API / "src/kefe_api/main.py"
MIGRATION = API / "migrations/versions/20260803_0025_public_provider_credential_mode.py"
TEST_MEMORY = API / "tests/test_public_provider_capture.py"
TEST_POSTGRES = API / "tests/test_public_provider_capture_postgres.py"
ADR = ROOT / "docs/adr/0087-public-provider-credential-mode-and-permit-bound-capture.md"
CONTRACT = ROOT / "docs/contracts/public-provider-capture-slice51.v1.json"
WORKFLOW = ROOT / ".github/workflows/public-provider-capture-ci.yml"

REQUIRED = (
    DOMAIN,
    CONTEXT,
    MEMORY,
    SECRET_EXECUTION,
    PUBLIC_EXECUTION,
    POSTGRES_ADMISSION,
    POSTGRES_CONTEXT,
    PIPELINE,
    MAIN,
    MIGRATION,
    TEST_MEMORY,
    TEST_POSTGRES,
    ADR,
    CONTRACT,
    WORKFLOW,
)


def fail(message: str) -> None:
    raise SystemExit(message)


def class_map(source: str) -> dict[str, ast.ClassDef]:
    tree = ast.parse(source)
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def dataclass_fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        child.target.id
        for child in node.body
        if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name)
    )


def method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for child in node.body:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    fail(f"{node.name}.{name} is missing")


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing public provider capture files: {missing}")

    domain = DOMAIN.read_text()
    context = CONTEXT.read_text()
    memory = MEMORY.read_text()
    secret_execution = SECRET_EXECUTION.read_text()
    public_execution = PUBLIC_EXECUTION.read_text()
    postgres_admission = POSTGRES_ADMISSION.read_text()
    postgres_context = POSTGRES_CONTEXT.read_text()
    pipeline = PIPELINE.read_text()
    main_source = MAIN.read_text()
    migration = MIGRATION.read_text()
    tests = TEST_MEMORY.read_text() + TEST_POSTGRES.read_text()
    adr = ADR.read_text()
    contract = json.loads(CONTRACT.read_text())
    workflow = WORKFLOW.read_text()

    if contract.get("contract") != "public-provider-capture-slice51":
        fail("public provider capture contract identity drifted")
    if contract.get("status") != "accepted":
        fail("public provider capture contract is not accepted")
    if contract.get("credential_modes") != ["PUBLIC", "SECRET_REF"]:
        fail("credential modes drifted")
    invariants = contract.get("capability_invariants", {})
    if invariants.get("public_secret_ref", "missing") is not None:
        fail("PUBLIC mode must have no secret reference")
    if invariants.get("secret_ref_mode_requires_reference") is not True:
        fail("SECRET_REF mode must require an opaque reference")
    public_contract = contract.get("public_executor", {})
    for forbidden_capability in (
        "secret_access",
        "auth_header_access",
        "network_access",
        "dns_access",
        "tls_access",
        "evidence_store_access",
        "autonomous_retry",
    ):
        if public_contract.get(forbidden_capability) is not False:
            fail(f"public executor capability must remain false: {forbidden_capability}")

    domain_classes = class_map(domain)
    mode = domain_classes.get("ProviderCredentialMode")
    if mode is None:
        fail("ProviderCredentialMode is missing")
    mode_values = {
        child.targets[0].id: child.value.value
        for child in mode.body
        if isinstance(child, ast.Assign)
        and isinstance(child.targets[0], ast.Name)
        and isinstance(child.value, ast.Constant)
    }
    if mode_values != {"PUBLIC": "PUBLIC", "SECRET_REF": "SECRET_REF"}:
        fail(f"ProviderCredentialMode drifted: {mode_values}")
    capability = domain_classes.get("SourceProviderCapability")
    if capability is None:
        fail("SourceProviderCapability is missing")
    fields = dataclass_fields(capability)
    if fields[:3] != ("adapter_code", "credential_mode", "secret_ref"):
        fail(f"provider capability credential fields drifted: {fields[:3]}")
    for fragment in (
        "PUBLIC provider capability cannot contain secret_ref",
        "SECRET_REF provider capability requires secret_ref",
        "self.credential_mode",
        "self.secret_ref",
    ):
        if fragment not in domain:
            fail(f"provider capability mode invariant missing: {fragment}")

    context_classes = class_map(context)
    execution_context = context_classes.get("ProviderPermitExecutionContext")
    if execution_context is None:
        fail("ProviderPermitExecutionContext is missing")
    context_fields = dataclass_fields(execution_context)
    if context_fields != (
        "permit_id",
        "adapter_code",
        "secret_ref",
        "permit_expires_at",
        "credential_mode",
    ):
        fail(f"permit context fields drifted: {context_fields}")
    if "secret_ref=<REDACTED>" not in context:
        fail("permit context must redact secret reference")

    public_classes = class_map(public_execution)
    public_adapter = public_classes.get("PublicSourceCaptureAdapter")
    if public_adapter is None or "Protocol" not in {
        ast.unparse(base) for base in public_adapter.bases
    }:
        fail("PublicSourceCaptureAdapter must be a Protocol")
    capture = method(public_adapter, "capture")
    capture_args = tuple(argument.arg for argument in capture.args.args)
    capture_kwonly = tuple(argument.arg for argument in capture.args.kwonlyargs)
    if capture_args != ("self",) or capture_kwonly != (
        "external_locator",
        "trace_id",
        "at",
    ):
        fail(
            "public adapter capture arguments must be exact locator, trace_id and at"
        )
    for class_name in (
        "InMemoryPublicSourceCaptureRegistry",
        "PermitBoundPublicCaptureExecutor",
        "CredentialModeRoutingProviderCaptureExecutor",
    ):
        if class_name not in public_classes:
            fail(f"public provider class is missing: {class_name}")

    for forbidden in (
        "SecretAccess",
        "use_bytes",
        "ProviderHttpAuth",
        "OwnedSensitiveHttpHeaders",
        "RawSourceEvidenceStore",
        "socket",
        "requests",
        "httpx",
        "urllib.request",
        "while True",
        "time.sleep",
    ):
        if forbidden in public_execution:
            fail(f"forbidden capability leaked into public executor: {forbidden}")

    public_position = secret_execution.find(
        "context.credential_mode is not ProviderCredentialMode.SECRET_REF"
    )
    resolver_position = secret_execution.find(
        "self._resolvers.get_for_reference(secret_ref)"
    )
    if not 0 <= public_position < resolver_position:
        fail("credentialed executor must reject PUBLIC before resolver lookup")

    for fragment in (
        "credential_mode=capability.credential_mode",
        "secret_ref=capability.secret_ref",
    ):
        if fragment not in memory:
            fail(f"memory permit context is missing: {fragment}")
    for fragment in (
        "credential_mode",
        "ProviderCredentialMode(row[\"credential_mode\"])",
    ):
        if fragment not in postgres_admission or fragment not in postgres_context:
            fail(f"PostgreSQL credential mode mapping is missing: {fragment}")

    for fragment in (
        'revision = "20260803_0025"',
        'down_revision = "20260802_0024"',
        "ADD COLUMN credential_mode text NOT NULL DEFAULT 'SECRET_REF'",
        "credential_mode = 'PUBLIC' AND secret_ref IS NULL",
        "credential_mode = 'SECRET_REF'",
        "cannot downgrade while PUBLIC provider capabilities exist",
    ):
        if fragment not in migration:
            fail(f"public provider migration invariant missing: {fragment}")

    for fragment in (
        "RssAtomSubscriptionManifestRegistry()",
        "build_rss_atom_public_capture_registry(",
        "PermitBoundPublicCaptureExecutor(",
        "CredentialModeRoutingProviderCaptureExecutor(",
        "capture_executor=provider_capture_executor",
    ):
        if fragment not in pipeline:
            fail(f"public provider composition missing: {fragment}")
    if "RssAtomSubscriptionManifest(" in pipeline or (
        "RssAtomSubscriptionManifest(" in main_source
    ):
        fail("production public provider composition contains a concrete feed manifest")
    if "rss_atom_subscription_activation_service.activate(" in pipeline or (
        "rss_atom_subscription_activation_service.activate(" in main_source
    ):
        fail("production startup must not activate a public provider")
    for fragment in (
        "app.state.public_capture_registry",
        "app.state.public_provider_capture_executor",
        "app.state.provider_capture_executor",
    ):
        if fragment not in main_source:
            fail(f"application public provider state missing: {fragment}")

    if contract.get("composition", {}).get(
        "production_public_adapters_registered"
    ) != 0:
        fail("production public adapter registry must remain empty")

    for test_name in (
        "test_provider_capability_credential_mode_cross_fields_are_exact",
        "test_public_executor_requires_exact_public_context_and_adapter",
        "test_public_and_credentialed_executors_reject_cross_mode_before_side_effects",
        "test_public_executor_rejects_invalid_permit_and_non_exact_result",
        "test_public_source_acquisition_uses_admission_and_completes_permit_before_write",
        "test_postgres_public_capability_and_active_context_are_mode_exact",
        "test_postgres_credential_mode_cross_field_constraints_fail_closed",
    ):
        if test_name not in tests:
            fail(f"public provider test evidence missing: {test_name}")

    for phrase in (
        "public providers require no credentials",
        "Production composition registers zero public adapters",
        "Downgrade refuses",
    ):
        if phrase not in adr:
            fail(f"ADR-0087 decision text missing: {phrase}")

    for phrase in (
        "Public provider capture architecture fitness",
        "Public provider capture behavior",
        "Public provider capture PostgreSQL",
        "check_public_provider_capture_contract.py",
    ):
        if phrase not in workflow:
            fail(f"public provider CI step missing: {phrase}")

    print("public provider capture contract: PASS")


if __name__ == "__main__":
    main()
