from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "services" / "api"
EVIDENCE = API_ROOT / "src/kefe_api/modules/knowledge/source_evidence.py"
CAPTURE = API_ROOT / "src/kefe_api/modules/knowledge/provider_http_evidence_capture.py"
SLICE48 = API_ROOT / "src/kefe_api/modules/knowledge/provider_http_capture.py"
STORE_TEST = API_ROOT / "tests/test_source_evidence.py"
CAPTURE_TEST = API_ROOT / "tests/test_provider_http_evidence_capture.py"
ARCH_TEST = API_ROOT / "tests/test_raw_source_evidence_architecture.py"
ADR = ROOT / "docs/adr/0085-immutable-raw-source-evidence-and-content-addressed-capture-assembly.md"
CONTRACT = ROOT / "docs/contracts/raw-source-evidence-slice49.v1.json"
WORKFLOW = ROOT / ".github/workflows/raw-source-evidence-ci.yml"

REQUIRED_FILES = (
    EVIDENCE,
    CAPTURE,
    SLICE48,
    STORE_TEST,
    CAPTURE_TEST,
    ARCH_TEST,
    ADR,
    CONTRACT,
    WORKFLOW,
)
FORBIDDEN_PROVIDER_NAMES = (
    "twitter",
    "youtube",
    "facebook",
    "instagram",
    "tiktok",
    "reddit",
)
FORBIDDEN_NETWORK_MODULES = (
    "socket",
    "ssl",
    "http.client",
    "requests",
    "httpx",
    "urllib.request",
)
SEAL_FIELDS = (
    "content_hash",
    "storage_ref",
    "byte_length",
    "media_type",
    "sealed_at",
)
PARSED_FIELDS = (
    "external_id",
    "canonical_url",
    "publisher_or_issuer",
    "published_at",
    "language_code",
    "jurisdiction_code",
)
FIXED_ERRORS = (
    "SOURCE_RAW_EVIDENCE_STORE_UNAVAILABLE",
    "SOURCE_RAW_EVIDENCE_STORE_FINAL",
    "SOURCE_RAW_EVIDENCE_CONTRACT_INVALID",
    "SOURCE_PROVIDER_HTTP_EVIDENCE_RESPONSE_INVALID",
)


def fail(message: str) -> None:
    raise SystemExit(message)


def _class_map(tree: ast.Module) -> dict[str, ast.ClassDef]:
    return {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}


def _method_map(node: ast.ClassDef) -> dict[str, ast.FunctionDef]:
    return {item.name: item for item in node.body if isinstance(item, ast.FunctionDef)}


def _fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        item.target.id
        for item in node.body
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
    )


def _arguments(method: ast.FunctionDef) -> tuple[str, ...]:
    return tuple(item.arg for item in (*method.args.args, *method.args.kwonlyargs))


def _annotation_text(method: ast.FunctionDef) -> str:
    parts: list[str] = []
    for argument in (*method.args.args, *method.args.kwonlyargs):
        if argument.annotation is not None:
            parts.append(ast.unparse(argument.annotation))
    if method.returns is not None:
        parts.append(ast.unparse(method.returns))
    return " ".join(parts)


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
        fail(f"missing raw source evidence files: {missing}")

    evidence_source = EVIDENCE.read_text()
    capture_source = CAPTURE.read_text()
    slice48_source = SLICE48.read_text()
    store_test_source = STORE_TEST.read_text()
    capture_test_source = CAPTURE_TEST.read_text()
    adr_source = ADR.read_text()
    contract = json.loads(CONTRACT.read_text())
    workflow_source = WORKFLOW.read_text()

    evidence_tree = ast.parse(evidence_source)
    capture_tree = ast.parse(capture_source)
    evidence_classes = _class_map(evidence_tree)
    capture_classes = _class_map(capture_tree)

    for source_name, source, tree in (
        ("evidence", evidence_source, evidence_tree),
        ("evidence capture", capture_source, capture_tree),
    ):
        lowered = source.lower()
        for provider_name in FORBIDDEN_PROVIDER_NAMES:
            if provider_name in lowered:
                fail(f"{source_name} contains provider-specific name: {provider_name}")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FORBIDDEN_NETWORK_MODULES:
                        fail(f"{source_name} imports network module: {alias.name}")
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module in FORBIDDEN_NETWORK_MODULES:
                    fail(f"{source_name} imports network module: {module}")
            if isinstance(node, ast.While):
                fail(f"{source_name} cannot implement autonomous retry")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "use_bytes"
            ):
                fail("evidence capture cannot read secret bytes")

    seal = evidence_classes.get("RawSourceEvidenceSeal")
    if seal is None or _fields(seal) != SEAL_FIELDS:
        fail("RawSourceEvidenceSeal fields drifted")
    if _dataclass_keywords(seal) != {
        "frozen": True,
        "slots": True,
        "repr": False,
    }:
        fail("RawSourceEvidenceSeal must be frozen, slotted and repr-redacted")

    store = evidence_classes.get("RawSourceEvidenceStore")
    if store is None or "Protocol" not in {ast.unparse(base) for base in store.bases}:
        fail("RawSourceEvidenceStore must be a Protocol")
    seal_method = _method_map(store).get("seal")
    if seal_method is None or _arguments(seal_method) != (
        "self",
        "adapter_code",
        "body",
        "media_type",
        "sealed_at",
    ):
        fail("RawSourceEvidenceStore.seal signature drifted")

    for class_name in (
        "InMemoryRawSourceEvidenceStore",
        "UnconfiguredRawSourceEvidenceStore",
        "RetryableRawSourceEvidenceError",
        "FinalRawSourceEvidenceError",
    ):
        if class_name not in evidence_classes:
            fail(f"raw source evidence class is missing: {class_name}")

    parsed = capture_classes.get("ProviderHttpParsedSource")
    if parsed is None or _fields(parsed) != PARSED_FIELDS:
        fail("ProviderHttpParsedSource fields drifted")
    if (
        "content_hash"
        in capture_source.split("class ProviderHttpParsedSource", 1)[1].split(
            "class EvidenceBackedProviderHttpCaptureDefinition", 1
        )[0]
    ):
        fail("ProviderHttpParsedSource cannot expose content_hash")
    if (
        "raw_storage_ref"
        in capture_source.split("class ProviderHttpParsedSource", 1)[1].split(
            "class EvidenceBackedProviderHttpCaptureDefinition", 1
        )[0]
    ):
        fail("ProviderHttpParsedSource cannot expose raw_storage_ref")

    definition = capture_classes.get("EvidenceBackedProviderHttpCaptureDefinition")
    if definition is None or "Protocol" not in {ast.unparse(base) for base in definition.bases}:
        fail("evidence-backed capture definition must be a Protocol")
    definition_methods = _method_map(definition)
    if set(definition_methods) != {
        "adapter_code",
        "build_plan",
        "parse_response",
    }:
        fail("evidence-backed definition method set drifted")
    annotations = " ".join(
        _annotation_text(definition_methods[name]) for name in ("build_plan", "parse_response")
    )
    for forbidden in (
        "SecretAccess",
        "RawSourceEvidenceStore",
        "RawSourceEvidenceSeal",
        "SensitiveHttpHeaderAccess",
        "ProviderDnsResolver",
        "PinnedHttpBackend",
    ):
        if forbidden in annotations:
            fail(f"evidence-backed definition exposes forbidden type: {forbidden}")

    adapter = capture_classes.get("EvidenceBackedProviderHttpCaptureAdapter")
    if adapter is None:
        fail("EvidenceBackedProviderHttpCaptureAdapter is missing")
    capture = _method_map(adapter).get("capture")
    if capture is None:
        fail("evidence-backed capture method is missing")
    capture_body = ast.get_source_segment(capture_source, capture) or ""
    ordered = (
        "build_plan(",
        "self._http_executor.execute(",
        "self._evidence_store.seal(",
        "parse_response(",
        "return CapturedSource(",
    )
    positions = tuple(capture_body.find(fragment) for fragment in ordered)
    if any(position < 0 for position in positions):
        fail("evidence-backed capture is missing an execution stage")
    if positions != tuple(sorted(positions)):
        fail("evidence-backed capture execution order drifted")
    for fragment in (
        "canonical_content_hash(response.body)",
        "content_hash=seal.content_hash",
        "raw_storage_ref=seal.storage_ref",
        "type(parsed) is not ProviderHttpParsedSource",
    ):
        if fragment not in capture_body:
            fail(f"evidence-backed capture guard is missing: {fragment}")
    for error_code in FIXED_ERRORS:
        if error_code not in capture_body:
            fail(f"evidence-backed capture error is missing: {error_code}")

    if "class ProviderHttpCaptureAdapter" not in slice48_source:
        fail("Slice 48 transitional primitive was removed")

    if contract.get("contract") != "raw-source-evidence-slice49":
        fail("raw source evidence contract identity drifted")
    if contract.get("status") != "accepted":
        fail("raw source evidence contract is not accepted")
    if contract.get("execution_order") != [
        "build_plan",
        "secure_http_execute",
        "seal_raw_evidence",
        "parse_bounded_response",
        "assemble_captured_source",
    ]:
        fail("raw source evidence execution order contract drifted")
    production = contract.get("production", {})
    if production != {
        "concrete_provider_definitions_registered": 0,
        "evidence_backed_adapters_registered": 0,
        "durable_evidence_backend_configured": False,
    }:
        fail("raw source evidence production boundary drifted")

    for phrase in (
        "KEFE computes lowercase SHA-256 over the exact response bytes",
        "`ProviderHttpParsedSource` is metadata-only",
        "Execution order is exact",
        "must use the evidence-backed path",
        "No production durability is claimed",
    ):
        if phrase not in adr_source:
            fail(f"ADR-0085 is missing decision text: {phrase}")

    for test_name in (
        "test_canonical_hash_reference_and_redacted_immutable_seal",
        "test_in_memory_store_is_content_addressed_idempotent_and_owns_bytes",
        "test_in_memory_store_fails_closed_on_injected_digest_collision",
        "test_unconfigured_store_is_bounded_retryable_and_redacted",
    ):
        if test_name not in store_test_source:
            fail(f"raw evidence store test evidence is missing: {test_name}")
    for test_name in (
        "test_metadata_type_cannot_supply_hash_or_storage_reference",
        "test_capture_orders_build_execute_seal_parse_and_assembles_canonical_source",
        "test_raw_evidence_is_sealed_before_parser_failure",
        "test_forged_or_non_seal_store_result_fails_before_parser",
        "test_factory_builds_registry_compatible_evidence_backed_adapter",
    ):
        if test_name not in capture_test_source:
            fail(f"evidence capture test evidence is missing: {test_name}")

    for phrase in (
        "Raw source evidence architecture fitness",
        "Raw source evidence behavior",
        "test_source_evidence.py",
        "test_provider_http_evidence_capture.py",
        "check_raw_source_evidence_contract.py",
    ):
        if phrase not in workflow_source:
            fail(f"raw source evidence CI is missing: {phrase}")

    print("raw source evidence contract: PASS")


if __name__ == "__main__":
    main()
