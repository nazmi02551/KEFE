from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
RUNTIME = API / "src/kefe_api/modules/knowledge/public_feed_runtime.py"
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
MAIN = API / "src/kefe_api/main.py"
TEST = API / "tests/test_public_feed_runtime.py"
ADR = (
    ROOT
    / "docs/adr/0090-validated-public-feed-definitions-and-manual-capture-runtime.md"
)
CONTRACT = ROOT / "docs/contracts/public-feed-runtime-slice54.v1.json"
WORKFLOW = ROOT / ".github/workflows/public-feed-runtime-ci.yml"

REQUIRED = (RUNTIME, PIPELINE, MAIN, TEST, ADR, CONTRACT, WORKFLOW)


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


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing public feed runtime files: {missing}")

    runtime = RUNTIME.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "public-feed-runtime-slice54":
        fail("public feed runtime contract identity drifted")
    if contract.get("status") != "accepted":
        fail("public feed runtime contract is not accepted")
    definition_contract = contract.get("definition", {})
    expected_definition = {
        "immutable": True,
        "versioned_feed_code": True,
        "versioned_adapter_code": True,
        "unique_feed_code": True,
        "unique_adapter_code": True,
        "https_only": True,
        "userinfo_allowed": False,
        "fragment_allowed": False,
        "non_443_port_allowed": False,
        "sensitive_query_names_allowed": False,
        "single_origin_profile": True,
        "credential_mode": "PUBLIC",
        "secret_ref": None,
        "parser": "STRICT_RSS_ATOM",
        "pipeline_code": "RSS_ATOM_FEED_ITEM_EXTRACTION",
        "pipeline_version": "1.0.0",
    }
    if definition_contract != expected_definition:
        fail(f"public feed definition contract drifted: {definition_contract}")

    classes = class_map(runtime)
    for class_name in (
        "PublicFeedDefinition",
        "PublicProviderCapabilityTemplate",
        "InMemoryPublicFeedDefinitionRegistry",
        "PublicFeedRuntimeBundle",
        "ManualPublicFeedCaptureService",
        "PublicFeedRuntimeError",
    ):
        if class_name not in classes:
            fail(f"public feed runtime class missing: {class_name}")

    definition = classes["PublicFeedDefinition"]
    if fields(definition) != (
        "feed_code",
        "display_name",
        "adapter_code",
        "external_locator",
        "parser_profile",
        "connect_timeout_ms",
        "read_timeout_ms",
        "total_timeout_ms",
        "max_response_bytes",
        "max_redirect_hops",
        "terms_evidence_ref",
        "rate_limit_evidence_ref",
        "quota_limit",
        "quota_window_seconds",
        "failure_threshold",
        "circuit_open_seconds",
        "permit_ttl_seconds",
        "language_code",
        "jurisdiction_code",
    ):
        fail("PublicFeedDefinition fields drifted")

    for fragment in (
        'parsed.scheme != "https"',
        "parsed.username is not None or parsed.password is not None",
        "port not in (None, 443)",
        "if parsed.fragment:",
        "normalized in _FORBIDDEN_QUERY_NAMES",
        "ProviderCredentialMode.PUBLIC",
        "secret_ref=None",
        "StrictRssAtomCaptureDefinition(",
        "build_feed_item_extraction_runtime(",
        "definition.acquisition_command()",
        "PUBLIC_FEED_DEFINITION_NOT_FOUND",
    ):
        if fragment not in runtime:
            fail(f"public feed runtime guard missing: {fragment}")

    capture_once = method(classes["ManualPublicFeedCaptureService"], "capture_once")
    capture_source = ast.get_source_segment(runtime, capture_once) or ""
    if capture_source.count("self._acquisition.acquire(") != 1:
        fail("manual feed capture must emit exactly one acquisition command")
    for forbidden in (
        "create_schedule(",
        "execute_pending_once(",
        "run_once(",
        "review_proposal(",
        "materialize_accepted_proposal(",
        "publish(",
        "add_claim(",
        "create_case",
        "requests",
        "httpx",
        "urllib.request",
        "socket",
    ):
        if forbidden in runtime:
            fail(f"forbidden behavior leaked into public feed runtime: {forbidden}")

    if "build_public_feed_runtime_bundle(" in pipeline or (
        "build_public_feed_runtime_bundle(" in main_source
    ):
        fail("production composition must not activate concrete public feeds")
    composition = contract.get("composition", {})
    if composition != {
        "production_concrete_feed_definitions_registered": 0,
        "production_public_feed_adapters_registered": 0,
        "production_feed_ingestion_plans_registered": 0,
        "preview_fallback": False,
        "live_network_in_tests": False,
    }:
        fail("public feed production composition contract drifted")

    for test_name in (
        "test_definition_derives_exact_public_profiles_and_stable_command",
        "test_definition_rejects_unsafe_locator_forms",
        "test_registry_rejects_order_duplicates_and_adapter_conflicts",
        "test_manual_service_emits_one_exact_acquisition_command",
        "test_bundle_rejects_empty_definitions",
        "test_full_manual_capture_and_ingestion_worker_vertical_path",
    ):
        if test_name not in tests:
            fail(f"public feed runtime test evidence missing: {test_name}")

    for phrase in (
        "immutable, versioned `PublicFeedDefinition`",
        "exact `ProviderAdoptionProfile`",
        "emits exactly one `SourceAcquisitionCommand`",
        "register zero concrete public feed definitions",
    ):
        if phrase not in adr:
            fail(f"ADR-0090 decision text missing: {phrase}")

    for phrase in (
        "Public feed runtime architecture fitness",
        "Public feed runtime behavior",
        "Parent feed item extraction architecture fitness",
        "check_public_feed_runtime_contract.py",
    ):
        if phrase not in workflow:
            fail(f"public feed runtime CI step missing: {phrase}")

    print("public feed runtime contract: PASS")


if __name__ == "__main__":
    main()
