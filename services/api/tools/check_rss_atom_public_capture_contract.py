from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "services/api"
PUBLIC_HTTP = API / "src/kefe_api/modules/knowledge/provider_public_http_capture.py"
RSS_ATOM = API / "src/kefe_api/modules/knowledge/rss_atom_capture.py"
PUBLIC_EXECUTION = API / "src/kefe_api/modules/knowledge/provider_public_execution.py"
PIPELINE = API / "src/kefe_api/infrastructure/editorial_pipeline.py"
MAIN = API / "src/kefe_api/main.py"
TEST = API / "tests/test_rss_atom_public_capture.py"
ADR = ROOT / "docs/adr/0088-strict-rss-atom-parsing-and-evidence-backed-public-http-capture.md"
CONTRACT = ROOT / "docs/contracts/rss-atom-public-capture-slice52.v1.json"
WORKFLOW = ROOT / ".github/workflows/rss-atom-public-capture-ci.yml"

REQUIRED = (
    PUBLIC_HTTP,
    RSS_ATOM,
    PUBLIC_EXECUTION,
    PIPELINE,
    MAIN,
    TEST,
    ADR,
    CONTRACT,
    WORKFLOW,
)


def fail(message: str) -> None:
    raise SystemExit(message)


def class_map(source: str) -> dict[str, ast.ClassDef]:
    tree = ast.parse(source)
    return {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}


def method(node: ast.ClassDef, name: str) -> ast.FunctionDef:
    for child in node.body:
        if isinstance(child, ast.FunctionDef) and child.name == name:
            return child
    fail(f"{node.name}.{name} is missing")


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED if not path.exists()]
    if missing:
        fail(f"missing RSS/Atom public capture files: {missing}")

    public_http = PUBLIC_HTTP.read_text(encoding="utf-8")
    rss_atom = RSS_ATOM.read_text(encoding="utf-8")
    pipeline = PIPELINE.read_text(encoding="utf-8")
    main_source = MAIN.read_text(encoding="utf-8")
    tests = TEST.read_text(encoding="utf-8")
    adr = ADR.read_text(encoding="utf-8")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if contract.get("contract") != "rss-atom-public-capture-slice52":
        fail("RSS/Atom public capture contract identity drifted")
    if contract.get("status") != "accepted":
        fail("RSS/Atom public capture contract is not accepted")
    capture = contract.get("capture", {})
    if capture.get("credential_mode") != "PUBLIC":
        fail("RSS/Atom capture must remain PUBLIC")
    if capture.get("credential_binding") is not False:
        fail("RSS/Atom public HTTP capture cannot use credential binding")
    if capture.get("evidence_before_parse") is not True:
        fail("RSS/Atom capture must seal evidence before parsing")
    if capture.get("parser_may_set_content_hash") is not False:
        fail("RSS/Atom parser cannot set trusted content hash")
    if capture.get("parser_may_set_storage_ref") is not False:
        fail("RSS/Atom parser cannot set trusted storage reference")

    formats = contract.get("formats", {})
    if formats.get("accepted") != ["ATOM_1_0", "RSS_2_0"]:
        fail("RSS/Atom accepted format set drifted")
    if formats.get("utf8_only") is not True:
        fail("RSS/Atom UTF-8-only policy drifted")
    unsafe = formats.get("unsafe_constructs", {})
    for name in (
        "doctype",
        "entity_declaration",
        "external_entity",
        "processing_instruction_after_declaration",
        "xinclude",
    ):
        if unsafe.get(name) is not False:
            fail(f"unsafe XML construct must remain disabled: {name}")

    profile = contract.get("default_parser_profile", {})
    expected_profile = {
        "max_document_bytes": 1_048_576,
        "max_elements": 4096,
        "max_depth": 16,
        "max_items": 256,
        "max_node_text_chars": 16_384,
        "max_total_text_chars": 262_144,
        "max_attributes_per_element": 8,
        "max_total_attribute_chars": 65_536,
        "max_metadata_field_chars": 4096,
    }
    if profile != expected_profile:
        fail(f"RSS/Atom default parser profile drifted: {profile}")

    public_classes = class_map(public_http)
    for class_name in (
        "FinalPublicHttpParseError",
        "EvidenceBackedPublicHttpCaptureDefinition",
        "EvidenceBackedPublicHttpCaptureAdapter",
        "EvidenceBackedPublicHttpCaptureAdapterFactory",
    ):
        if class_name not in public_classes:
            fail(f"public HTTP capture class is missing: {class_name}")
    definition = public_classes["EvidenceBackedPublicHttpCaptureDefinition"]
    parse_method = method(definition, "parse_response")
    parse_kwonly = tuple(item.arg for item in parse_method.args.kwonlyargs)
    if parse_kwonly != ("plan", "response", "trace_id", "at"):
        fail(f"public HTTP parser arguments drifted: {parse_kwonly}")

    transport_position = public_http.find("self._transport.execute(plan.request)")
    evidence_position = public_http.find("self._evidence_store.seal(")
    parse_position = public_http.find("self._definition.parse_response(")
    if not 0 <= transport_position < evidence_position < parse_position:
        fail("public HTTP transport/evidence/parser order drifted")
    for forbidden in (
        "SecretAccess",
        "ProviderHttpCredentialBinding",
        "OwnedSensitiveHttpHeaders",
        "SecureProviderHttpExecutor",
        "use_bytes",
        "credential=",
        "import requests",
        "import httpx",
        "urllib.request",
        "socket",
        "while True",
        "time.sleep",
    ):
        if forbidden in public_http:
            fail(f"credential/network authority leaked into public HTTP adapter: {forbidden}")

    rss_classes = class_map(rss_atom)
    for class_name in (
        "StrictRssAtomParseProfile",
        "StrictRssAtomCaptureDefinition",
    ):
        if class_name not in rss_classes:
            fail(f"RSS/Atom class is missing: {class_name}")
    for fragment in (
        'ATOM_NAMESPACE = "http://www.w3.org/2005/Atom"',
        'XINCLUDE_NAMESPACE = "http://www.w3.org/2001/XInclude"',
        'if b"<!doctype" in lowered or b"<!entity" in lowered:',
        'if b"<?" in remaining:',
        'body.decode("utf-8-sig")',
        "ElementTree.fromstring(response.body)",
        "SOURCE_PUBLIC_HTTP_PARSE_PROFILE_EXCEEDED",
        "SOURCE_PUBLIC_HTTP_PARSE_TIMESTAMP_INVALID",
        "canonical_url=plan.request.url",
    ):
        if fragment not in rss_atom:
            fail(f"RSS/Atom parser invariant missing: {fragment}")
    for forbidden in (
        "requests",
        "httpx",
        "urllib.request",
        "socket",
        "lxml",
        "defusedxml",
        "html.unescape",
        "BeautifulSoup",
        "eval(",
        "exec(",
    ):
        if forbidden in rss_atom:
            fail(f"excluded dependency/behavior leaked into RSS/Atom parser: {forbidden}")

    if "MutablePublicSourceCaptureRegistry()" not in pipeline:
        fail("production public adapter registry must remain empty")
    if (
        "StrictRssAtomCaptureDefinition(" in pipeline
        or "StrictRssAtomCaptureDefinition(" in main_source
    ):
        fail("production composition must not register an RSS/Atom adapter")
    if contract.get("composition", {}).get("production_rss_atom_adapters_registered") != 0:
        fail("contract must keep production RSS/Atom adapter registry empty")

    for test_name in (
        "test_rss_capture_seals_before_parse_and_uses_trusted_evidence",
        "test_atom_capture_returns_feed_level_metadata_only",
        "test_parser_rejects_unsafe_or_invalid_xml",
        "test_parser_enforces_item_depth_text_and_document_budgets",
        "test_parser_rejects_invalid_timestamp_media_type_and_required_fields",
        "test_transport_and_evidence_failures_stop_before_parse",
        "test_public_permit_to_http_evidence_to_source_artifact_vertical_slice",
    ):
        if test_name not in tests:
            fail(f"RSS/Atom test evidence missing: {test_name}")

    for phrase in (
        "raw HTTP body is sealed",
        "DTD",
        "feed snapshot",
        "registers zero RSS/Atom adapters",
    ):
        if phrase not in adr:
            fail(f"ADR-0088 decision text missing: {phrase}")

    for phrase in (
        "RSS Atom public capture architecture fitness",
        "RSS Atom public capture behavior",
        "Parent public provider capture architecture fitness",
        "check_rss_atom_public_capture_contract.py",
    ):
        if phrase not in workflow:
            fail(f"RSS/Atom CI step missing: {phrase}")

    print("RSS Atom public capture contract: PASS")


if __name__ == "__main__":
    main()
