from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "services" / "api"
BACKEND = API_ROOT / "src/kefe_api/modules/knowledge/source_evidence_backend.py"
RUNTIME = API_ROOT / "src/kefe_api/infrastructure/raw_evidence_runtime.py"
SETTINGS = API_ROOT / "src/kefe_api/core/settings.py"
MAIN = API_ROOT / "src/kefe_api/main.py"
TEST_BACKEND = API_ROOT / "tests/test_source_evidence_backend.py"
TEST_RUNTIME = API_ROOT / "tests/test_raw_evidence_runtime.py"
ADR = ROOT / "docs/adr/0086-durable-raw-evidence-backend-capability-and-no-fallback-runtime.md"
CONTRACT = ROOT / "docs/contracts/durable-raw-evidence-backend-slice50.v1.json"
WORKFLOW = ROOT / ".github/workflows/durable-raw-evidence-backend-ci.yml"

REQUIRED_FILES = (
    BACKEND,
    RUNTIME,
    SETTINGS,
    MAIN,
    TEST_BACKEND,
    TEST_RUNTIME,
    ADR,
    CONTRACT,
    WORKFLOW,
)
FORBIDDEN_VENDOR_NAMES = (
    "amazon",
    "aws",
    "s3",
    "google cloud",
    "gcs",
    "azure",
    "minio",
)
FORBIDDEN_NETWORK_MODULES = (
    "boto",
    "botocore",
    "google.cloud",
    "azure.storage",
    "requests",
    "httpx",
    "socket",
)
PROFILE_FIELDS = (
    "profile_code",
    "backend_code",
    "namespace",
    "max_object_bytes",
    "write_timeout_ms",
    "read_timeout_ms",
    "atomic_put_if_absent",
    "immutable_objects",
    "read_after_write_verification",
    "capability_evidence_ref",
)
FIXED_ERROR_CODES = (
    "RAW_EVIDENCE_BACKEND_TIMEOUT",
    "RAW_EVIDENCE_BACKEND_UNAVAILABLE",
    "RAW_EVIDENCE_BACKEND_CONTRACT_INVALID",
    "RAW_EVIDENCE_READ_AFTER_WRITE_MISSING",
    "RAW_EVIDENCE_READ_AFTER_WRITE_MISMATCH",
)


def fail(message: str) -> None:
    raise SystemExit(message)


def _class_map(tree: ast.Module) -> dict[str, ast.ClassDef]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def _method_names(node: ast.ClassDef) -> set[str]:
    return {
        item.name
        for item in node.body
        if isinstance(item, ast.FunctionDef)
    }


def _field_names(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        item.target.id
        for item in node.body
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
    )


def _dataclass_keywords(node: ast.ClassDef) -> dict[str, object]:
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        if ast.unparse(decorator.func) != "dataclass":
            continue
        return {
            keyword.arg: keyword.value.value
            for keyword in decorator.keywords
            if keyword.arg is not None and isinstance(keyword.value, ast.Constant)
        }
    return {}


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        fail(f"missing durable raw evidence files: {missing}")

    backend_source = BACKEND.read_text()
    runtime_source = RUNTIME.read_text()
    settings_source = SETTINGS.read_text()
    main_source = MAIN.read_text()
    tests_source = TEST_BACKEND.read_text() + TEST_RUNTIME.read_text()
    adr_source = ADR.read_text()
    contract = json.loads(CONTRACT.read_text())
    workflow_source = WORKFLOW.read_text()
    tree = ast.parse(backend_source)
    classes = _class_map(tree)

    lowered = (backend_source + runtime_source).lower()
    for vendor_name in FORBIDDEN_VENDOR_NAMES:
        if vendor_name in lowered:
            fail(f"durable raw evidence runtime contains vendor name: {vendor_name}")
    for forbidden_module in FORBIDDEN_NETWORK_MODULES:
        if forbidden_module in lowered:
            fail(
                "durable raw evidence runtime imports or names network SDK: "
                f"{forbidden_module}"
            )
    if "InMemoryRawSourceEvidenceStore" in runtime_source:
        fail("runtime composition must never import the in-memory raw evidence store")
    if "while " in backend_source:
        fail("durable raw evidence store cannot implement autonomous retry loops")

    profile = classes.get("RawEvidenceBackendProfile")
    if profile is None:
        fail("RawEvidenceBackendProfile is missing")
    if _field_names(profile) != PROFILE_FIELDS:
        fail(f"RawEvidenceBackendProfile fields drifted: {_field_names(profile)}")
    if _dataclass_keywords(profile) != {"frozen": True, "slots": True}:
        fail("RawEvidenceBackendProfile must be frozen and slotted")

    backend = classes.get("RawEvidenceBackend")
    if backend is None or "Protocol" not in {ast.unparse(base) for base in backend.bases}:
        fail("RawEvidenceBackend must be a Protocol")
    if _method_names(backend) != {"backend_code", "put_if_absent", "read_exact"}:
        fail("RawEvidenceBackend operation set drifted")

    store = classes.get("DurableRawSourceEvidenceStore")
    if store is None:
        fail("DurableRawSourceEvidenceStore is missing")
    seal = next(
        (
            item
            for item in store.body
            if isinstance(item, ast.FunctionDef) and item.name == "seal"
        ),
        None,
    )
    if seal is None:
        fail("DurableRawSourceEvidenceStore.seal is missing")
    seal_source = ast.get_source_segment(backend_source, seal) or ""
    ordered = (
        "canonical_content_hash(",
        "put_if_absent(",
        "read_exact(",
        "RawSourceEvidenceSeal(",
    )
    positions = tuple(seal_source.find(fragment) for fragment in ordered)
    if any(position < 0 for position in positions) or positions != tuple(sorted(positions)):
        fail("durable raw evidence order must be hash, put, read, seal")
    for fragment in (
        "write_result.object_key != object_key",
        "read_result.object_key != object_key",
        "read_result.body != owned_body",
        "read_result.media_type != canonical_media_type",
    ):
        if fragment not in seal_source:
            fail(f"durable raw evidence verification is missing: {fragment}")
    for error_code in FIXED_ERROR_CODES:
        if error_code not in backend_source:
            fail(f"durable raw evidence bounded error is missing: {error_code}")

    for mode in ("DISABLED", "EXTERNAL_DURABLE"):
        if mode not in settings_source or mode not in contract.get("runtime_modes", []):
            fail(f"raw evidence runtime mode is missing: {mode}")
    for phrase in (
        "InMemoryRawEvidenceBackendProfileRegistry()",
        "InMemoryRawEvidenceBackendRegistry()",
        "RAW_EVIDENCE_PROFILE_FORBIDDEN_WHEN_DISABLED",
        "RAW_EVIDENCE_BACKEND_PROFILE_REQUIRED",
        "RAW_EVIDENCE_BACKEND_PROFILE_NOT_REGISTERED",
        "RAW_EVIDENCE_BACKEND_NOT_REGISTERED",
    ):
        if phrase not in runtime_source:
            fail(f"raw evidence no-fallback runtime is missing: {phrase}")

    for phrase in (
        "build_raw_source_evidence_store(settings)",
        "app.state.raw_source_evidence_store",
    ):
        if phrase not in main_source:
            fail(f"application raw evidence composition is missing: {phrase}")

    if contract.get("contract") != "durable-raw-evidence-backend-slice50":
        fail("durable raw evidence contract identity drifted")
    if contract.get("status") != "accepted":
        fail("durable raw evidence contract is not accepted")
    composition = contract.get("composition", {})
    if composition.get("production_profiles_registered") != 0:
        fail("production durable raw evidence profiles must remain empty")
    if composition.get("production_backends_registered") != 0:
        fail("production durable raw evidence backends must remain empty")
    if composition.get("external_in_memory_fallback") is not False:
        fail("external durable mode cannot fall back to memory")
    if composition.get("external_disabled_fallback") is not False:
        fail("external durable mode cannot fall back to disabled storage")

    for phrase in (
        "never silently fall back to process memory",
        "always reads the object back",
        "registers zero durable profiles and zero durable backends",
    ):
        if phrase not in adr_source:
            fail(f"ADR-0086 is missing required decision text: {phrase}")

    for test_name in (
        "test_store_orders_atomic_put_read_verification_and_returns_canonical_seal",
        "test_existing_object_is_idempotent_and_still_read_back_verified",
        "test_missing_or_mismatched_read_after_write_fails_closed",
        "test_external_mode_requires_exact_registered_profile_and_backend",
        "test_external_mode_builds_only_exact_durable_store_without_fallback",
    ):
        if test_name not in tests_source:
            fail(f"durable raw evidence test evidence is missing: {test_name}")

    for phrase in (
        "Durable raw evidence backend architecture fitness",
        "Durable raw evidence backend behavior",
        "check_durable_raw_evidence_backend_contract.py",
    ):
        if phrase not in workflow_source:
            fail(f"durable raw evidence CI is missing: {phrase}")

    print("durable raw evidence backend contract: PASS")


if __name__ == "__main__":
    main()
