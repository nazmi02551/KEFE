from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "services" / "api"
MODULE = API_ROOT / "src/kefe_api/modules/knowledge/provider_http_capture.py"
COMPOSITION = API_ROOT / "src/kefe_api/infrastructure/editorial_pipeline.py"
TEST = API_ROOT / "tests/test_provider_http_capture.py"
ARCH_TEST = API_ROOT / "tests/test_provider_http_capture_architecture.py"
ADR = ROOT / "docs/adr/0084-provider-neutral-http-capture-adapter-and-bounded-response-parsing.md"
CONTRACT = ROOT / "docs/contracts/provider-http-capture-slice48.v1.json"
WORKFLOW = ROOT / ".github/workflows/provider-http-capture-ci.yml"

REQUIRED_FILES = (MODULE, COMPOSITION, TEST, ARCH_TEST, ADR, CONTRACT, WORKFLOW)
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
FORBIDDEN_DEFINITION_TYPES = (
    "SecretAccess",
    "SecretLease",
    "SensitiveHttpHeaderAccess",
    "ProviderDnsResolver",
    "PinnedHttpBackend",
    "socket",
    "SSLContext",
)
FIXED_ERROR_CODES = (
    "SOURCE_PROVIDER_HTTP_PLAN_INVALID",
    "SOURCE_PROVIDER_HTTP_ADAPTER_MISMATCH",
    "SOURCE_PROVIDER_HTTP_EXECUTION_INVALID",
    "SOURCE_PROVIDER_HTTP_RESPONSE_INVALID",
)


def fail(message: str) -> None:
    raise SystemExit(message)


def _class_map(tree: ast.Module) -> dict[str, ast.ClassDef]:
    return {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}


def _method_map(node: ast.ClassDef) -> dict[str, ast.FunctionDef]:
    return {item.name: item for item in node.body if isinstance(item, ast.FunctionDef)}


def _argument_names(method: ast.FunctionDef) -> tuple[str, ...]:
    positional = tuple(item.arg for item in method.args.args)
    keyword_only = tuple(item.arg for item in method.args.kwonlyargs)
    return positional + keyword_only


def _annotation_text(method: ast.FunctionDef) -> str:
    fragments: list[str] = []
    for argument in (*method.args.args, *method.args.kwonlyargs):
        if argument.annotation is not None:
            fragments.append(ast.unparse(argument.annotation))
    if method.returns is not None:
        fragments.append(ast.unparse(method.returns))
    return " ".join(fragments)


def _dataclass_keywords(node: ast.ClassDef) -> dict[str, object]:
    for decorator in node.decorator_list:
        if not isinstance(decorator, ast.Call):
            continue
        rendered = ast.unparse(decorator.func)
        if rendered != "dataclass":
            continue
        values: dict[str, object] = {}
        for keyword in decorator.keywords:
            if keyword.arg is not None and isinstance(keyword.value, ast.Constant):
                values[keyword.arg] = keyword.value.value
        return values
    return {}


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        fail(f"missing provider HTTP capture files: {missing}")

    module_source = MODULE.read_text()
    composition_source = COMPOSITION.read_text()
    test_source = TEST.read_text()
    adr_source = ADR.read_text()
    contract = json.loads(CONTRACT.read_text())
    workflow_source = WORKFLOW.read_text()
    tree = ast.parse(module_source)
    classes = _class_map(tree)

    lowered = module_source.lower()
    for provider_name in FORBIDDEN_PROVIDER_NAMES:
        if provider_name in lowered:
            fail(f"provider HTTP capture contains provider-specific name: {provider_name}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in FORBIDDEN_NETWORK_MODULES:
                    fail(f"provider HTTP capture imports network module: {alias.name}")
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in FORBIDDEN_NETWORK_MODULES:
                fail(f"provider HTTP capture imports network module: {module}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "use_bytes":
                fail("generic provider HTTP capture wrapper must not call SecretAccess.use_bytes")
        if isinstance(node, ast.While):
            fail("provider HTTP capture wrapper cannot implement an autonomous retry loop")

    plan = classes.get("ProviderHttpCapturePlan")
    if plan is None:
        fail("ProviderHttpCapturePlan is missing")
    plan_fields = tuple(
        item.target.id
        for item in plan.body
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
    )
    if plan_fields != ("adapter_code", "request"):
        fail(f"ProviderHttpCapturePlan fields drifted: {plan_fields}")
    dataclass_keywords = _dataclass_keywords(plan)
    if dataclass_keywords != {"frozen": True, "slots": True, "repr": False}:
        fail("ProviderHttpCapturePlan must be frozen, slotted and repr-redacted")

    definition = classes.get("ProviderHttpCaptureDefinition")
    if definition is None:
        fail("ProviderHttpCaptureDefinition is missing")
    if "Protocol" not in {ast.unparse(base) for base in definition.bases}:
        fail("ProviderHttpCaptureDefinition must be a Protocol")
    definition_methods = _method_map(definition)
    if set(definition_methods) != {"adapter_code", "build_plan", "parse_response"}:
        fail("ProviderHttpCaptureDefinition method set drifted")
    if _argument_names(definition_methods["build_plan"]) != (
        "self",
        "external_locator",
        "trace_id",
        "at",
    ):
        fail("ProviderHttpCaptureDefinition.build_plan signature drifted")
    if _argument_names(definition_methods["parse_response"]) != (
        "self",
        "plan",
        "response",
        "trace_id",
        "at",
    ):
        fail("ProviderHttpCaptureDefinition.parse_response signature drifted")
    definition_annotations = " ".join(
        _annotation_text(definition_methods[name]) for name in ("build_plan", "parse_response")
    )
    for forbidden_type in FORBIDDEN_DEFINITION_TYPES:
        if forbidden_type in definition_annotations:
            fail(f"ProviderHttpCaptureDefinition exposes forbidden type: {forbidden_type}")

    adapter = classes.get("ProviderHttpCaptureAdapter")
    if adapter is None:
        fail("ProviderHttpCaptureAdapter is missing")
    adapter_methods = _method_map(adapter)
    capture = adapter_methods.get("capture")
    if capture is None:
        fail("ProviderHttpCaptureAdapter.capture is missing")
    if _argument_names(capture) != (
        "self",
        "external_locator",
        "trace_id",
        "secret",
        "at",
    ):
        fail("ProviderHttpCaptureAdapter.capture signature drifted")
    capture_source = ast.get_source_segment(module_source, capture) or ""
    ordered_fragments = (
        "build_plan(",
        "self._http_executor.execute(",
        "parse_response(",
    )
    positions = tuple(capture_source.find(fragment) for fragment in ordered_fragments)
    if any(position < 0 for position in positions) or positions != tuple(sorted(positions)):
        fail("provider HTTP capture order must be plan, execute, parse")
    for fragment in (
        "secret=secret",
        "type(response) is not ProviderHttpResponse",
        "type(captured) is not CapturedSource",
    ):
        if fragment not in capture_source:
            fail(f"provider HTTP capture is missing required guard: {fragment}")
    for error_code in FIXED_ERROR_CODES:
        if error_code not in capture_source:
            fail(f"provider HTTP capture is missing bounded error: {error_code}")

    factory = classes.get("ProviderHttpCaptureAdapterFactory")
    if factory is None or "create" not in _method_map(factory):
        fail("ProviderHttpCaptureAdapterFactory.create is missing")

    if contract.get("contract") != "provider-http-capture-slice48":
        fail("provider HTTP capture contract identity drifted")
    if contract.get("status") != "accepted":
        fail("provider HTTP capture contract is not accepted")
    limits = contract.get("limits", {})
    if limits != {
        "max_external_locator_chars": 4096,
        "max_trace_id_chars": 128,
        "requests_per_capture": 1,
        "autonomous_retries": 0,
    }:
        fail("provider HTTP capture limits drifted")
    factory_contract = contract.get("factory", {})
    if factory_contract.get("production_definitions_registered") != 0:
        fail("production provider HTTP definitions must remain empty")
    if factory_contract.get("production_adapters_registered") != 0:
        fail("production provider HTTP adapters must remain empty")
    invariants = "\n".join(contract.get("invariants", ()))
    for phrase in (
        "cannot read or resolve secret material",
        "cannot perform DNS, TLS, socket, redirect or retry work",
        "validated before secret use or HTTP execution",
        "No live external request is required or claimed",
    ):
        if phrase not in invariants:
            fail(f"provider HTTP capture contract is missing invariant: {phrase}")

    for phrase in (
        "Provider-specific code must be limited to two deterministic responsibilities",
        "passes it directly to `SecureProviderHttpExecutor`",
        "Planning completes and is validated before any secret callback",
        "No autonomous retry occurs in this adapter",
        "registers zero provider definitions and zero credential-aware HTTP adapters",
    ):
        if phrase not in adr_source:
            fail(f"ADR-0084 is missing required decision text: {phrase}")

    for fragment in (
        "InMemoryCredentialAwareSourceCaptureRegistry()",
        "MutableProviderAdoptionRegistry()",
        "InMemoryProviderHttpAuthRegistry()",
    ):
        if fragment not in composition_source:
            fail(f"production empty-registry composition drifted: {fragment}")

    for test_name in (
        "test_plan_is_immutable_redacted_and_requires_exact_request_adapter",
        "test_capture_orders_plan_execute_parse_and_wrapper_never_reads_secret",
        "test_invalid_inputs_are_bounded_before_plan_or_execution",
        "test_http_error_classification_and_bounded_code_are_preserved",
        "test_parser_failure_and_non_exact_captured_source_are_final_bounded",
        "test_factory_builds_structural_credential_adapter_for_existing_registry",
    ):
        if test_name not in test_source:
            fail(f"provider HTTP capture test evidence is missing: {test_name}")

    for phrase in (
        "Provider HTTP capture architecture fitness",
        "Provider HTTP capture behavior",
        "test_provider_http_capture.py",
        "check_provider_http_capture_contract.py",
    ):
        if phrase not in workflow_source:
            fail(f"provider HTTP capture CI is missing required step/path: {phrase}")

    print("provider HTTP capture contract: PASS")


if __name__ == "__main__":
    main()
