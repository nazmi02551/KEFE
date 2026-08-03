from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "services" / "api"
RUNTIME = API_ROOT / "src/kefe_api/infrastructure/provider_http_runtime.py"
SETTINGS = API_ROOT / "src/kefe_api/core/settings.py"
COMPOSITION = API_ROOT / "src/kefe_api/infrastructure/editorial_pipeline.py"
TEST = API_ROOT / "tests/test_provider_pinned_runtime.py"
ADR = ROOT / "docs/adr/0082-pinned-dns-tls-runtime-and-explicit-egress-activation.md"
CONTRACT = ROOT / "docs/contracts/provider-pinned-runtime-slice46.v1.json"
WORKFLOW = ROOT / ".github/workflows/provider-pinned-runtime-ci.yml"

REQUIRED_FILES = (RUNTIME, SETTINGS, COMPOSITION, TEST, ADR, CONTRACT, WORKFLOW)
FORBIDDEN_RUNTIME_FRAGMENTS = (
    "import requests",
    "from requests",
    "import httpx",
    "from httpx",
    "urllib.request",
    "os.environ",
    "getproxies",
    "ProxyHandler",
    "set_tunnel",
    "cookiejar",
    "follow_redirects",
    "allow_redirects",
    "CERT_NONE",
    "check_hostname = False",
    "ssl._create_unverified_context",
)
FORBIDDEN_PROVIDER_NAMES = (
    "twitter",
    "youtube",
    "facebook",
    "instagram",
    "tiktok",
    "reddit",
)
REQUIRED_RUNTIME_FRAGMENTS = (
    "class SystemProviderDnsResolver",
    "class PinnedTlsHttpBackend",
    "class _ExactIpHttpsConnection",
    "(self._target_ip, self.port)",
    "server_hostname=self.host",
    "context.minimum_version = ssl.TLSVersion.TLSv1_2",
    "context.check_hostname = True",
    "context.verify_mode = ssl.CERT_REQUIRED",
    "context.options |= ssl.OP_NO_COMPRESSION",
    'connection.putheader("Connection", "close")',
    'connection.putheader("Accept-Encoding", "identity")',
    "skip_host=True",
    "skip_accept_encoding=True",
    "response.read(request.max_response_bytes + 1)",
    '"content-type"',
    '"etag"',
    '"last-modified"',
    '"location"',
    '"retry-after"',
    'if mode == "DISABLED"',
    'if mode == "PINNED_TLS"',
)
REQUIRED_SETTINGS_FRAGMENTS = (
    'provider_http_runtime_mode: Literal["DISABLED", "PINNED_TLS"] = "DISABLED"',
    "provider_http_dns_max_answers: int = Field(default=16, ge=1, le=64)",
    "provider_http_ca_bundle_path: str | None = None",
)
REQUIRED_COMPOSITION_FRAGMENTS = (
    "RssAtomSubscriptionManifestRegistry()",
    "build_rss_atom_provider_adoption_registry(",
    "provider_http_runtime = build_provider_http_runtime(settings)",
    "dns_resolver=provider_http_runtime.dns_resolver",
    "backend=provider_http_runtime.backend",
)


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    missing = [str(path.relative_to(ROOT)) for path in REQUIRED_FILES if not path.exists()]
    if missing:
        fail(f"missing provider pinned runtime files: {missing}")

    runtime_source = RUNTIME.read_text()
    settings_source = SETTINGS.read_text()
    composition_source = COMPOSITION.read_text()
    test_source = TEST.read_text()
    adr_source = ADR.read_text()
    contract = json.loads(CONTRACT.read_text())
    workflow_source = WORKFLOW.read_text()

    for fragment in FORBIDDEN_RUNTIME_FRAGMENTS:
        if fragment in runtime_source:
            fail(f"provider pinned runtime contains forbidden fragment: {fragment}")
    lowered_runtime = runtime_source.lower()
    for provider_name in FORBIDDEN_PROVIDER_NAMES:
        if provider_name in lowered_runtime:
            fail(f"provider pinned runtime contains provider-specific name: {provider_name}")
    for fragment in REQUIRED_RUNTIME_FRAGMENTS:
        if fragment not in runtime_source:
            fail(f"provider pinned runtime is missing required fragment: {fragment}")
    for fragment in REQUIRED_SETTINGS_FRAGMENTS:
        if fragment not in settings_source:
            fail(f"provider pinned runtime setting drifted: {fragment}")
    for fragment in REQUIRED_COMPOSITION_FRAGMENTS:
        if fragment not in composition_source:
            fail(f"provider pinned runtime composition drifted: {fragment}")
    if "RssAtomSubscriptionManifest(" in composition_source:
        fail("provider pinned runtime composition contains a concrete feed manifest")
    if "rss_atom_subscription_activation_service.activate(" in composition_source:
        fail("provider pinned runtime composition auto-activates egress")

    if contract.get("contract") != "provider-pinned-runtime-slice46":
        fail("provider pinned runtime contract identity drifted")
    if contract.get("status") != "accepted":
        fail("provider pinned runtime contract is not accepted")
    if contract.get("default_runtime_mode") != "DISABLED":
        fail("provider pinned runtime default mode drifted")
    if contract.get("runtime_modes") != ["DISABLED", "PINNED_TLS"]:
        fail("provider pinned runtime mode set drifted")
    if contract.get("composition", {}).get("provider_profiles_registered") != 0:
        fail("provider pinned runtime must keep adoption registry empty")
    invariants = "\n".join(contract.get("invariants", ()))
    for phrase in (
        "exact selected IP",
        "exact approved host",
        "No proxy, cookie, redirect, CONNECT tunnel or ambient credential",
        "does not require or claim a live external provider call",
    ):
        if phrase not in invariants:
            fail(f"provider pinned runtime contract is missing invariant: {phrase}")

    for phrase in (
        "exact `target_ip`",
        "approved request host as SNI",
        "TLS 1.2 is the minimum",
        "does not authorize any provider",
        "No live external request is required or claimed",
    ):
        if phrase not in adr_source:
            fail(f"ADR-0082 is missing required decision text: {phrase}")

    for phrase in (
        "test_system_dns_returns_all_deduplicated_candidates_without_authorizing",
        "test_exact_ip_connection_uses_selected_ip_and_approved_host_sni",
        "test_backend_emits_exact_bounded_http11_request_and_projects_headers",
        "test_backend_enforces_content_length_and_max_plus_one_body_read",
        "test_backend_maps_connect_tls_read_and_protocol_failures",
    ):
        if phrase not in test_source:
            fail(f"provider pinned runtime test evidence is missing: {phrase}")

    for phrase in (
        "Provider pinned runtime architecture fitness",
        "Provider pinned runtime behavior",
        "test_provider_pinned_runtime.py",
        "check_provider_pinned_runtime_contract.py",
    ):
        if phrase not in workflow_source:
            fail(f"provider pinned runtime CI is missing required step/path: {phrase}")

    print("provider pinned runtime contract: PASS")


if __name__ == "__main__":
    main()
