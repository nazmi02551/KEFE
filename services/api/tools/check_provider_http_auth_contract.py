from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "services" / "api"
AUTH = API_ROOT / "src/kefe_api/modules/knowledge/provider_http_auth.py"
TRANSPORT = API_ROOT / "src/kefe_api/modules/knowledge/provider_http_transport.py"
RUNTIME = API_ROOT / "src/kefe_api/infrastructure/provider_http_runtime.py"
COMPOSITION = API_ROOT / "src/kefe_api/infrastructure/editorial_pipeline.py"
TEST = API_ROOT / "tests/test_provider_http_auth.py"
ADR = ROOT / "docs/adr/0083-ephemeral-provider-http-authentication-and-origin-bound-decoration.md"
CONTRACT = ROOT / "docs/contracts/provider-http-auth-slice47.v1.json"
WORKFLOW = ROOT / ".github/workflows/provider-http-auth-ci.yml"

REQUIRED_FILES = (
    AUTH,
    TRANSPORT,
    RUNTIME,
    COMPOSITION,
    TEST,
    ADR,
    CONTRACT,
    WORKFLOW,
)
FORBIDDEN_AUTH_FRAGMENTS = (
    ".decode(",
    "str(secret",
    "repr(secret",
    "logging.",
    "print(secret",
    "os.environ",
    "base64",
    "urlencode",
    "query=secret",
)
FORBIDDEN_PROVIDER_NAMES = (
    "twitter",
    "youtube",
    "facebook",
    "instagram",
    "tiktok",
    "reddit",
)
REQUIRED_AUTH_FRAGMENTS = (
    "class ProviderHttpAuthScheme",
    'BEARER_AUTHORIZATION = "BEARER_AUTHORIZATION"',
    'HEADER_TOKEN = "HEADER_TOKEN"',
    "class ProviderHttpAuthProfile",
    "class InMemoryProviderHttpAuthRegistry",
    "class OwnedSensitiveHttpHeaders",
    "memoryview(value).toreadonly()",
    "for index in range(len(value))",
    "value[index] = 0",
    "raise TypeError(\"sensitive HTTP header comparison is forbidden\")",
    "raise TypeError(\"sensitive HTTP header serialization is forbidden\")",
    "secret.use_bytes(use_secret, at=at)",
    "envelope.close()",
    "except ProviderHttpError:",
    '"PROVIDER_HTTP_AUTH_PROFILE_NOT_REGISTERED"',
    '"PROVIDER_HTTP_AUTH_SECRET_INVALID"',
    '"PROVIDER_HTTP_AUTH_SECRET_UNAVAILABLE"',
)
REQUIRED_TRANSPORT_FRAGMENTS = (
    "class SensitiveHttpHeaderAccess",
    "class ProviderHttpCredentialBinding",
    "credential: ProviderHttpCredentialBinding | None = None",
    "sensitive_headers: SensitiveHttpHeaderAccess | None",
    "credential.credential_origin not in profile.allowed_origins",
    '"PROVIDER_HTTP_AUTH_ORIGIN_NOT_ALLOWED"',
    "if origin != credential.credential_origin",
    '"PROVIDER_HTTP_AUTH_REDIRECT_BLOCKED"',
    "sensitive_headers=sensitive_headers",
)
REQUIRED_RUNTIME_FRAGMENTS = (
    "def _send_request_headers(",
    "request.sensitive_headers.use_headers(emit_sensitive)",
    "connection.putheader(normalized, bytes(value))",
    "connection.endheaders()",
    '"PROVIDER_HTTP_AUTH_HEADERS_INVALID"',
    '"PROVIDER_HTTP_AUTH_HEADERS_UNAVAILABLE"',
)
REQUIRED_COMPOSITION_FRAGMENTS = (
    "InMemoryProviderHttpAuthRegistry()",
    "SecureProviderHttpExecutor(",
    "auth_registry=provider_http_auth_registry",
    "transport=provider_http_transport",
    "provider_http_auth_registry=provider_http_auth_registry",
    "secure_provider_http_executor=secure_provider_http_executor",
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
    "auth_scheme",
    "credential_origin",
    "header_name",
    "credential",
    "secret",
    "authorization",
}
EXPECTED_OUTBOUND_FIELDS = {
    "adapter_code",
    "method",
    "url",
    "public_headers",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def class_annotations(source: str, class_name: str) -> set[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.target.id
                for child in node.body
                if isinstance(child, ast.AnnAssign)
                and isinstance(child.target, ast.Name)
            }
    fail(f"class annotations not found: {class_name}")
    return set()


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
        fail(f"missing provider HTTP auth files: {missing}")

    auth_source = AUTH.read_text()
    transport_source = TRANSPORT.read_text()
    runtime_source = RUNTIME.read_text()
    composition_source = COMPOSITION.read_text()
    test_source = TEST.read_text()
    adr_source = ADR.read_text()
    contract = json.loads(CONTRACT.read_text())
    workflow_source = WORKFLOW.read_text()

    for fragment in FORBIDDEN_AUTH_FRAGMENTS:
        if fragment in auth_source:
            fail(f"provider HTTP auth contains forbidden secret handling: {fragment}")
    lowered = "\n".join((auth_source, transport_source, runtime_source)).lower()
    for provider_name in FORBIDDEN_PROVIDER_NAMES:
        if provider_name in lowered:
            fail(f"provider HTTP auth boundary contains provider-specific name: {provider_name}")
    for fragment in REQUIRED_AUTH_FRAGMENTS:
        if fragment not in auth_source:
            fail(f"provider HTTP auth module is missing: {fragment}")
    for fragment in REQUIRED_TRANSPORT_FRAGMENTS:
        if fragment not in transport_source:
            fail(f"provider HTTP transport auth boundary is missing: {fragment}")
    for fragment in REQUIRED_RUNTIME_FRAGMENTS:
        if fragment not in runtime_source:
            fail(f"provider pinned backend auth boundary is missing: {fragment}")
    for fragment in REQUIRED_COMPOSITION_FRAGMENTS:
        if fragment not in composition_source:
            fail(f"provider HTTP auth composition is missing: {fragment}")

    outbound_fields = class_annotations(transport_source, "OutboundHttpRequest")
    if outbound_fields != EXPECTED_OUTBOUND_FIELDS:
        fail(f"OutboundHttpRequest fields drifted: {sorted(outbound_fields)}")

    keys = operational_keys(transport_source)
    if keys != EXPECTED_OPERATIONAL_KEYS:
        fail(f"provider HTTP operational keys drifted: {sorted(keys)}")
    if keys & FORBIDDEN_OPERATIONAL_KEYS:
        fail("provider HTTP operational result exposes auth material")

    if contract.get("contract") != "provider-http-auth-slice47":
        fail("provider HTTP auth contract identity drifted")
    if contract.get("status") != "accepted":
        fail("provider HTTP auth contract is not accepted")
    if contract.get("auth_schemes") != [
        "BEARER_AUTHORIZATION",
        "HEADER_TOKEN",
    ]:
        fail("provider HTTP auth scheme set drifted")
    if contract.get("production_composition", {}).get("auth_registry") != "empty":
        fail("provider HTTP auth registry must remain empty")
    if contract.get("production_composition", {}).get("real_auth_profile") is not False:
        fail("provider HTTP auth contract cannot claim a real auth profile")
    if contract.get("operational_result", {}).get("unchanged") is not True:
        fail("provider HTTP operational schema must remain unchanged")

    invariants = "\n".join(contract.get("invariants", ()))
    for phrase in (
        "SecretAccess.use_bytes",
        "never decoded to text",
        "one exact canonical HTTPS origin",
        "cross-origin redirect fails",
        "ends headers inside the sensitive access callback",
        "Production auth and provider adoption registries remain empty",
    ):
        if phrase not in invariants:
            fail(f"provider HTTP auth contract is missing invariant: {phrase}")

    for phrase in (
        "callback-scoped `SecretAccess.use_bytes`",
        "fails closed before another backend request",
        "zeroizes its owned buffer",
        "does not claim deterministic erasure",
        "empty auth-profile registry",
    ):
        if phrase not in adr_source:
            fail(f"ADR-0083 is missing required decision text: {phrase}")

    for phrase in (
        "test_owned_sensitive_headers_are_redacted_scoped_and_zeroized",
        "test_secure_executor_applies_bearer_header_and_closes_envelope",
        "test_same_origin_redirect_reuses_sensitive_access_within_budget",
        "test_cross_origin_redirect_is_blocked_before_second_dns_or_backend_call",
        "test_pinned_backend_sends_and_ends_sensitive_headers_inside_callback",
    ):
        if phrase not in test_source:
            fail(f"provider HTTP auth test evidence is missing: {phrase}")

    for phrase in (
        "Provider HTTP authentication architecture fitness",
        "Provider HTTP authentication behavior",
        "test_provider_http_auth.py",
        "check_provider_http_auth_contract.py",
    ):
        if phrase not in workflow_source:
            fail(f"provider HTTP auth CI is missing required step/path: {phrase}")

    print("provider HTTP auth contract: PASS")


if __name__ == "__main__":
    main()
