from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
ACTIVATION = API / "src/kefe_api/modules/knowledge/public_feed_activation.py"
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
MAIN = API / "src/kefe_api/main.py"
TEST = API / "tests/test_public_feed_activation.py"
ADR = (
    ROOT
    / "docs/adr/0090-immutable-public-feed-activation-and-scheduled-capture-handoff.md"
)
CONTRACT = ROOT / "docs/contracts/public-feed-activation-slice54.v1.json"
WORKFLOW = ROOT / ".github/workflows/public-feed-activation-ci.yml"

REQUIRED = (ACTIVATION, PIPELINE, MAIN, TEST, ADR, CONTRACT, WORKFLOW)


def fail(message: str) -> None:
    raise SystemExit(message)


def class_map(source: str) -> dict[str, ast.ClassDef]:
    tree = ast.parse(source)
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        child.target.id
        for child in node.body
        if isinstance(child, ast.AnnAssign)
        and isinstance(child.target, ast.Name)
    )


def method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for child in node.body:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    fail(f"{node.name}.{name} is missing")


def dataclass_keywords(node: ast.ClassDef) -> dict[str, object]:
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and ast.unparse(decorator.func) == "dataclass":
            return {
                keyword.arg: keyword.value.value
                for keyword in decorator.keywords
                if keyword.arg is not None
                and isinstance(keyword.value, ast.Constant)
            }
    return {}


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing public feed activation files: {missing}")

    source = ACTIVATION.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "public-feed-activation-slice54":
        fail("public feed activation contract identity drifted")
    if contract.get("status") != "accepted":
        fail("public feed activation contract is not accepted")
    activation_contract = contract.get("activation", {})
    if activation_contract.get("configuration_hash") != "sha256-canonical-json":
        fail("activation configuration hash contract drifted")
    if activation_contract.get("runtime_registry_mutation") is not False:
        fail("activation bundle cannot mutate running registries")
    if activation_contract.get("network_during_bundle_build") is not False:
        fail("activation bundle build cannot perform network access")
    if activation_contract.get("preview_fallback") is not False:
        fail("activation preview fallback is forbidden")

    provider = contract.get("provider", {})
    expected_provider = {
        "credential_mode": "PUBLIC",
        "secret_ref": False,
        "lifecycle": "ENABLED",
        "initial_quota_count": 0,
        "initial_failure_count": 0,
        "initial_circuit_state": "CLOSED",
        "allowed_methods": ["GET"],
        "single_exact_origin": True,
        "https_only": True,
        "userinfo": False,
        "non_443_port": False,
        "fragment": False,
        "credential_named_query_parameters": False,
    }
    if provider != expected_provider:
        fail(f"public feed provider contract drifted: {provider}")

    binding = contract.get("parser_transport_binding", {})
    if binding.get("http_media_types_equal_parser_media_types") is not True:
        fail("HTTP and parser media types must remain exact")
    if binding.get("http_response_bytes_equal_parser_document_bytes") is not True:
        fail("HTTP and parser byte budgets must remain exact")
    if binding.get("evidence_backed_public_adapter") is not True:
        fail("public feed activation must use evidence-backed adapters")

    classes = class_map(source)
    expected_fields = {
        "PublicFeedScheduleSeed": (
            "activation_code",
            "adapter_code",
            "external_locator",
            "configuration_hash",
            "first_due_at",
            "interval_seconds",
            "max_dispatch_attempts",
            "taxonomy_version",
            "methodology_version",
            "locale",
            "jurisdiction_code",
        ),
        "PublicFeedActivationDefinition": (
            "activation_code",
            "adapter_code",
            "external_locator",
            "adoption_profile",
            "parser_profile",
            "capability",
            "first_due_at",
            "interval_seconds",
            "max_dispatch_attempts",
            "taxonomy_version",
            "methodology_version",
            "locale",
            "jurisdiction_code",
        ),
        "PublicFeedActivationBundle": (
            "activation_registry",
            "adoption_registry",
            "public_capture_registry",
            "provider_http_transport",
            "capabilities",
            "schedule_seeds",
        ),
    }
    for class_name, class_fields in expected_fields.items():
        node = classes.get(class_name)
        if node is None or fields(node) != class_fields:
            fail(f"{class_name} fields drifted")
        if dataclass_keywords(node) != {"frozen": True, "slots": True}:
            fail(f"{class_name} must be frozen and slotted")

    registry = classes.get("PublicFeedActivationRegistry")
    if registry is None or "Protocol" not in {
        ast.unparse(base) for base in registry.bases
    }:
        fail("PublicFeedActivationRegistry must be a Protocol")
    for class_name in (
        "InMemoryPublicFeedActivationRegistry",
        "PublicFeedActivationBundleFactory",
    ):
        if class_name not in classes:
            fail(f"public feed activation class missing: {class_name}")

    definition = classes["PublicFeedActivationDefinition"]
    post_init = ast.get_source_segment(source, method(definition, "__post_init__")) or ""
    for fragment in (
        "self.adoption_profile.adapter_code != self.adapter_code",
        "self.capability.adapter_code != self.adapter_code",
        "self.adoption_profile.allowed_origins != (origin,)",
        "self.adoption_profile.allowed_methods != (ProviderHttpMethod.GET,)",
        "self.adoption_profile.allowed_media_types",
        "self.parser_profile.accepted_media_types",
        "self.adoption_profile.max_response_bytes",
        "self.parser_profile.max_document_bytes",
        "self.capability.credential_mode is not ProviderCredentialMode.PUBLIC",
        "self.capability.secret_ref is not None",
        "self.capability.lifecycle_state is not ProviderCapabilityLifecycle.ENABLED",
        "self.parser_profile.max_items > MAX_PROPOSALS",
    ):
        if fragment not in post_init:
            fail(f"activation invariant missing: {fragment}")

    for fragment in (
        "parse_qsl(parsed.query, keep_blank_values=True)",
        "credential-like query parameter is forbidden",
        'return f"sha256:{sha256(encoded).hexdigest()}"',
        '"pipeline_code": PIPELINE_CODE',
        '"pipeline_version": PIPELINE_VERSION',
        "configuration_hash=self.configuration_hash",
    ):
        if fragment not in source:
            fail(f"activation configuration guard missing: {fragment}")

    factory = classes["PublicFeedActivationBundleFactory"]
    build_source = ast.get_source_segment(source, method(factory, "build")) or ""
    ordered_fragments = (
        "InMemoryPublicFeedActivationRegistry(ordered)",
        "InMemoryProviderAdoptionRegistry(",
        "ControlledProviderHttpTransport(",
        "EvidenceBackedPublicHttpCaptureAdapterFactory(",
        "adapter_factory.create(item.capture_definition())",
        "InMemoryPublicSourceCaptureRegistry(adapters)",
        "return PublicFeedActivationBundle(",
    )
    positions = tuple(build_source.find(fragment) for fragment in ordered_fragments)
    if any(position < 0 for position in positions) or positions != tuple(sorted(positions)):
        fail("activation bundle composition order drifted")
    for forbidden in (
        ".execute(",
        ".capture(",
        ".create_schedule(",
        ".create_or_get(",
        "requests",
        "httpx",
        "urllib.request",
        "socket",
        "while True",
    ):
        if forbidden in build_source:
            fail(f"bundle build contains forbidden side effect: {forbidden}")

    if "InMemoryPublicSourceCaptureRegistry()" not in pipeline:
        fail("production public capture registry must remain empty")
    if "InMemoryIngestionWorkerRuntimeRegistry()" not in pipeline:
        fail("production ingestion worker registry must remain empty")
    for forbidden in (
        "PublicFeedActivationDefinition(",
        "PublicFeedActivationBundleFactory(",
        "build_feed_item_extraction_runtime(",
    ):
        if forbidden in pipeline or forbidden in main_source:
            fail(f"production composition activated public feed behavior: {forbidden}")
    production = contract.get("production", {})
    if production != {
        "public_feed_activations_registered": 0,
        "rss_atom_public_adapters_registered": 0,
        "feed_item_runtime_plans_registered": 0,
        "concrete_external_feeds": 0,
    }:
        fail("public feed activation production boundary drifted")

    for test_name in (
        "test_activation_is_immutable_and_configuration_hash_is_canonical",
        "test_activation_rejects_identity_policy_parser_and_locator_drift",
        "test_activation_requires_clean_public_secret_free_capability",
        "test_registry_and_bundle_reject_duplicate_activation_or_adapter",
        "test_bundle_uses_one_exact_adoption_registry_for_controlled_transport",
        "test_full_schedule_to_capture_to_ingestion_worker_vertical_path",
    ):
        if test_name not in tests:
            fail(f"public feed activation test evidence missing: {test_name}")

    for phrase in (
        "one immutable `PublicFeedActivationDefinition`",
        "canonical lowercase SHA-256 configuration hash",
        "pre-start composition primitive",
        "due schedule -> provider admission permit",
        "registers zero public feed activations",
    ):
        if phrase not in adr:
            fail(f"ADR-0090 decision text missing: {phrase}")

    for phrase in (
        "Public feed activation architecture fitness",
        "Public feed activation behavior",
        "Parent RSS Atom architecture fitness",
        "Parent feed item extraction architecture fitness",
        "Parent source scheduler architecture fitness",
        "check_public_feed_activation_contract.py",
    ):
        if phrase not in workflow:
            fail(f"public feed activation CI step missing: {phrase}")

    print("public feed activation contract: PASS")


if __name__ == "__main__":
    main()
