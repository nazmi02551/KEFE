from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "services" / "api"
MODULE = API_ROOT / "src/kefe_api/modules/knowledge/provider_http_transport.py"
COMPOSITION = API_ROOT / "src/kefe_api/infrastructure/editorial_pipeline.py"
TEST = API_ROOT / "tests/test_provider_http_transport.py"
ADR = ROOT / "docs/adr/0081-controlled-outbound-http-and-provider-adoption-conformance.md"
CONTRACT = ROOT / "docs/contracts/provider-http-transport-slice45.v1.json"
WORKFLOW = ROOT / ".github/workflows/provider-http-transport-ci.yml"

REQUIRED_FILES = (MODULE, COMPOSITION, TEST, ADR, CONTRACT, WORKFLOW)
FORBIDDEN_MODULE_FRAGMENTS = (
    "import requests",
    "from requests",
    "import httpx",
    "from httpx",
    "import socket",
    "from socket",
    "import ssl",
    "from ssl",
    "urllib.request",
    "trust_env",
    "follow_redirects",
    "allow_redirects",
    "playwright",
    "selenium",
    "subprocess",
    "os.environ",
)
FORBIDDEN_PROVIDER_NAMES = (
    "twitter",
    "youtube",
    "facebook",
    "instagram",
    "tiktok",
    "reddit",
)
REQUIRED_MODULE_FRAGMENTS = (
    "class ProviderAdoptionProfile",
    "class InMemoryProviderAdoptionRegistry",
    "class OutboundHttpRequest",
    "class PinnedOutboundHttpRequest",
    "class ProviderDnsResolver",
    "class PinnedHttpBackend",
    "class ControlledProviderHttpTransport",
    "not address.is_global",
    "address.is_loopback",
    "address.is_private",
    "address.is_link_local",
    "address.is_multicast",
    "address.is_reserved",
    "address.is_unspecified",
    "sorted(\n            set(parsed_addresses)",
    "target_ip=target_ip",
    "urljoin(current_url, location)",
    "PROVIDER_HTTP_TARGET_NOT_PUBLIC",
    "PROVIDER_HTTP_REDIRECT_BLOCKED",
    "PROVIDER_HTTP_RESPONSE_TOO_LARGE",
    "PROVIDER_HTTP_TOTAL_BUDGET_EXCEEDED",
    "def as_operational_dict",
)
REQUIRED_COMPOSITION_FRAGMENTS = (
    "InMemoryProviderAdoptionRegistry()",
    "UnconfiguredProviderDnsResolver()",
    "UnconfiguredPinnedHttpBackend()",
    "provider_http_transport=provider_http_transport",
)
EXPECTED_OPERATIONAL_KEYS = {
    "outcome",
    "adapter_code",
    "method",
    "status_code",
    "redirect_hops",
    "response_bytes",
    "elapsed_ms",
    "error_code",
}
FORBIDDEN_OPERATIONAL_KEYS = {
    "url",
    "origin",
    "host",
    "target_ip",
    "request_target",
    "headers",
    "credential",
    "secret",
    "body",
    "response_text",
    "exception",
    "location",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def operational_keys(source: str) -> set[str]:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "as_operational_dict":
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Dict):
                keys = {
                    key.value
                    for key in child.keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                }
                if keys:
                    return keys
    fail("provider HTTP operational dictionary was not found")
    return set()


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        fail(f"missing provider HTTP transport files: {missing}")

    module_source = MODULE.read_text()
    composition_source = COMPOSITION.read_text()
    test_source = TEST.read_text()
    adr_source = ADR.read_text()
    contract = json.loads(CONTRACT.read_text())
    workflow_source = WORKFLOW.read_text()

    for fragment in FORBIDDEN_MODULE_FRAGMENTS:
        if fragment in module_source:
            fail(f"provider HTTP module contains forbidden runtime fragment: {fragment}")
    lowered_module = module_source.lower()
    for provider_name in FORBIDDEN_PROVIDER_NAMES:
        if provider_name in lowered_module:
            fail(f"provider HTTP module contains provider-specific name: {provider_name}")
    for fragment in REQUIRED_MODULE_FRAGMENTS:
        if fragment not in module_source:
            fail(f"provider HTTP module is missing required fragment: {fragment}")
    for fragment in REQUIRED_COMPOSITION_FRAGMENTS:
        if fragment not in composition_source:
            fail(f"provider HTTP production composition is missing: {fragment}")

    keys = operational_keys(module_source)
    if keys != EXPECTED_OPERATIONAL_KEYS:
        fail(f"provider HTTP operational keys drifted: {sorted(keys)}")
    if keys & FORBIDDEN_OPERATIONAL_KEYS:
        fail("provider HTTP operational result exposes a forbidden field")

    if contract.get("contract") != "provider-http-transport-slice45":
        fail("provider HTTP contract identity drifted")
    if contract.get("status") != "accepted":
        fail("provider HTTP contract is not accepted")
    if set(contract.get("operational_allowlist", ())) != EXPECTED_OPERATIONAL_KEYS:
        fail("provider HTTP contract operational allowlist drifted")
    invariants = "\n".join(contract.get("invariants", ())).lower()
    for phrase in (
        "https",
        "globally routable",
        "pinned ip",
        "never follows redirects",
        "empty or unconfigured",
    ):
        if phrase not in invariants:
            fail(f"provider HTTP contract is missing invariant: {phrase}")

    for phrase in (
        "DNS rebinding",
        "one hop at a time",
        "Production composition remains inert",
        "without claiming external provider compliance",
    ):
        if phrase not in adr_source:
            fail(f"ADR-0081 is missing required decision text: {phrase}")

    for phrase in (
        "test_non_public_dns_targets_are_rejected",
        "test_mixed_public_and_private_dns_answers_fail_closed",
        "test_public_address_selection_is_deterministic_and_pinned",
        "test_redirect_is_revalidated_resolved_and_repinned_per_hop",
        "test_operational_result_is_exact_allowlist",
    ):
        if phrase not in test_source:
            fail(f"provider HTTP test evidence is missing: {phrase}")

    for phrase in (
        "Provider HTTP transport architecture fitness",
        "Provider HTTP transport behavior",
        "test_provider_http_transport.py",
        "check_provider_http_transport_contract.py",
    ):
        if phrase not in workflow_source:
            fail(f"provider HTTP CI is missing required step/path: {phrase}")

    print("provider HTTP transport contract: PASS")


if __name__ == "__main__":
    main()
